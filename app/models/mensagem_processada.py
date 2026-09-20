from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime
from app.core.database import Base
from datetime import datetime, timezone


class MensagemProcessada(Base):
    __tablename__ = "mensagens_processadas"
    message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
