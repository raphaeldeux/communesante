from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class Severite(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Indicateur(Base):
    __tablename__ = "indicateurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commune_id: Mapped[int] = mapped_column(Integer, ForeignKey("communes.id"), nullable=False)
    annee: Mapped[int] = mapped_column(Integer, nullable=False)
    code_indicateur: Mapped[str] = mapped_column(String(100), nullable=False)
    valeur: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    date_calcul: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    commune: Mapped["Commune"] = relationship("Commune", back_populates="indicateurs")  # noqa: F821


class Alerte(Base):
    __tablename__ = "alertes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commune_id: Mapped[int] = mapped_column(Integer, ForeignKey("communes.id"), nullable=False)
    annee: Mapped[int] = mapped_column(Integer, nullable=False)
    indicateur: Mapped[str] = mapped_column(String(100), nullable=False)
    severite: Mapped[Severite] = mapped_column(Enum(Severite), nullable=False, default=Severite.WARNING)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolue: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    commune: Mapped["Commune"] = relationship("Commune", back_populates="alertes")  # noqa: F821
