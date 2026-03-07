from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Commune(Base):
    __tablename__ = "communes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_insee: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    siret: Mapped[str | None] = mapped_column(String(14), nullable=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    departement: Mapped[str | None] = mapped_column(String(3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    exercices: Mapped[list["ExerciceFinancier"]] = relationship(  # noqa: F821
        "ExerciceFinancier", back_populates="commune", cascade="all, delete-orphan"
    )
    indicateurs: Mapped[list["Indicateur"]] = relationship(  # noqa: F821
        "Indicateur", back_populates="commune", cascade="all, delete-orphan"
    )
    alertes: Mapped[list["Alerte"]] = relationship(  # noqa: F821
        "Alerte", back_populates="commune", cascade="all, delete-orphan"
    )
