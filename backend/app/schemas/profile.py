import json
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    major: str
    interests: list[str]
    skills: list[str]
    experience_level: str
    savings: float
    updated_at: datetime

    @field_validator("interests", "skills", mode="before")
    @classmethod
    def _coerce_json_str(cls, v: Any) -> Any:
        """Parse JSON-encoded strings back to lists (SQLite compat).

        SQLAlchemy's ARRAY(Text) on SQLite returns the stored JSON string
        iterated as a list of characters (e.g. '[]' -> ['[', ']']).
        Detect that case by re-joining and JSON-parsing.
        """
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(v, list):
            # Check if the list looks like JSON characters (SQLite ARRAY quirk)
            joined = "".join(str(c) for c in v)
            if joined and joined[0] in ("[", "{"):
                try:
                    parsed = json.loads(joined)
                    if isinstance(parsed, list):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    pass
        return v


class ProfileUpdate(BaseModel):
    major: str | None = None
    interests: list[str] | None = None
    skills: list[str] | None = None
    experience_level: Literal["entry", "mid", "senior"] | None = None
    savings: float | None = None
