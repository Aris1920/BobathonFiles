"""Test fixtures for the career-debt-planner backend.

Uses an in-memory SQLite database so tests run without a live PostgreSQL instance.
DATABASE_URL is overridden via an environment variable *before* the app modules are
imported so that the module-level create_engine() call in database.py uses SQLite.

SQLite does not natively support PostgreSQL's ARRAY type.  We handle this with two
complementary patches that are applied once at import time:

1. ``@compiles(ARRAY, "sqlite")`` — makes SQLAlchemy emit ``JSON`` in the
   CREATE TABLE DDL instead of the PostgreSQL-specific ``ARRAY`` syntax.
2. ``before_cursor_execute`` engine event — serialises any Python ``list``
   parameters to JSON strings before they reach the SQLite driver (which only
   accepts strings, ints, floats, bytes, and None).
"""
from __future__ import annotations

import json
import os
from typing import Any

# ---------------------------------------------------------------------------
# Override DATABASE_URL *before* any app module is imported so that the
# module-level create_engine() call in database.py also uses SQLite.
# ---------------------------------------------------------------------------
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.dialects.postgresql import ARRAY  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402

# ---------------------------------------------------------------------------
# 1. DDL patch — compile ARRAY as JSON in CREATE TABLE statements.
# ---------------------------------------------------------------------------

@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(type_, compiler, **kw):  # noqa: ARG001
    return "JSON"


# ---------------------------------------------------------------------------
# Import app modules *after* the patches above are in place.
# ---------------------------------------------------------------------------

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Build a test-only engine and DML patch.
# ---------------------------------------------------------------------------

_SQLITE_URL = "sqlite://"

_test_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(_test_engine, "before_cursor_execute", retval=True)
def _serialize_lists(conn, cursor, statement, parameters, context, executemany):
    """Serialise Python list values to JSON strings for SQLite."""
    if parameters is None:
        return statement, parameters

    def _fix(val: Any) -> Any:
        return json.dumps(val) if isinstance(val, list) else val

    if executemany:
        # SQLAlchemy 2.x "insertmanyvalues" fires this event with
        # executemany=True but passes a flat tuple (not a list of row-tuples)
        # when it has merged multiple rows into a single VALUES(...),(...)
        # statement.  Detect that case: if parameters is a sequence whose
        # first element is NOT itself iterable (i.e. it's a scalar value like
        # str/int/float), treat the whole thing as a single flat param tuple.
        if parameters and not isinstance(parameters[0], (list, tuple)):
            parameters = tuple(_fix(v) for v in parameters)
        else:
            parameters = [tuple(_fix(v) for v in row) for row in parameters]
    elif isinstance(parameters, (list, tuple)):
        parameters = tuple(_fix(v) for v in parameters)
    elif isinstance(parameters, dict):
        parameters = {k: _fix(v) for k, v in parameters.items()}

    return statement, parameters


_TestSessionLocal = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def db_session(_create_tables) -> Session:
    """Yield a transactional session that is rolled back after each test."""
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = _TestSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _make_get_db_override(session: Session):
    """Return a get_db dependency override yielding *session*."""
    def _get_db():
        try:
            yield session
        finally:
            pass
    return _get_db


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient with get_db overridden to use the test SQLite session."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
