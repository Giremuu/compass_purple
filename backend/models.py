import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Run(Base):
    """Stores the history of every module execution."""
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_type: Mapped[str] = mapped_column(String(16))   # red / blue / purple / utility
    module_name: Mapped[str] = mapped_column(String(64))
    params: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    result: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    status: Mapped[str] = mapped_column(String(16))          # success / error
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def params_dict(self) -> dict:
        return json.loads(self.params)

    def result_dict(self) -> dict:
        return json.loads(self.result)


class Source(Base):
    """External tool links displayed on the Sources page."""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(32))  # red / blue / purple / utility
