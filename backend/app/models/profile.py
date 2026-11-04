from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

ExperienceLevelEnum = Enum(
    "entry", "mid", "senior", name="experience_level_enum"
)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    major: Mapped[str] = mapped_column(String, nullable=False)
    interests: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    skills: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    experience_level: Mapped[str] = mapped_column(
        ExperienceLevelEnum, nullable=False, default="entry"
    )
    savings: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
