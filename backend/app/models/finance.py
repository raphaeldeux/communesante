from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class SourceDonnee(str, enum.Enum):
    API = "API"
    PDF = "PDF"
    MANUEL = "MANUEL"


class StatutExercice(str, enum.Enum):
    BROUILLON = "BROUILLON"
    VALIDE = "VALIDE"
    SYNCHRONISE = "SYNCHRONISE"


class ExerciceFinancier(Base):
    __tablename__ = "exercices_financiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commune_id: Mapped[int] = mapped_column(Integer, ForeignKey("communes.id"), nullable=False)
    annee: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[SourceDonnee] = mapped_column(
        Enum(SourceDonnee), nullable=False, default=SourceDonnee.API
    )
    statut: Mapped[StatutExercice] = mapped_column(
        Enum(StatutExercice), nullable=False, default=StatutExercice.BROUILLON
    )
    fichier_pdf: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    commune: Mapped["Commune"] = relationship("Commune", back_populates="exercices")  # noqa: F821
    recettes_fonctionnement: Mapped[list["RecetteFonctionnement"]] = relationship(
        "RecetteFonctionnement", back_populates="exercice", cascade="all, delete-orphan"
    )
    depenses_fonctionnement: Mapped[list["DepenseFonctionnement"]] = relationship(
        "DepenseFonctionnement", back_populates="exercice", cascade="all, delete-orphan"
    )
    recettes_investissement: Mapped[list["RecetteInvestissement"]] = relationship(
        "RecetteInvestissement", back_populates="exercice", cascade="all, delete-orphan"
    )
    depenses_investissement: Mapped[list["DepenseInvestissement"]] = relationship(
        "DepenseInvestissement", back_populates="exercice", cascade="all, delete-orphan"
    )


class RecetteFonctionnement(Base):
    __tablename__ = "recettes_fonctionnement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exercice_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercices_financiers.id"), nullable=False)
    chapitre: Mapped[str] = mapped_column(String(10), nullable=False)
    article: Mapped[str | None] = mapped_column(String(10), nullable=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant_vote: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    montant_reel: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    exercice: Mapped["ExerciceFinancier"] = relationship(
        "ExerciceFinancier", back_populates="recettes_fonctionnement"
    )


class DepenseFonctionnement(Base):
    __tablename__ = "depenses_fonctionnement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exercice_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercices_financiers.id"), nullable=False)
    chapitre: Mapped[str] = mapped_column(String(10), nullable=False)
    article: Mapped[str | None] = mapped_column(String(10), nullable=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant_vote: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    montant_reel: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    exercice: Mapped["ExerciceFinancier"] = relationship(
        "ExerciceFinancier", back_populates="depenses_fonctionnement"
    )


class RecetteInvestissement(Base):
    __tablename__ = "recettes_investissement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exercice_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercices_financiers.id"), nullable=False)
    chapitre: Mapped[str] = mapped_column(String(10), nullable=False)
    article: Mapped[str | None] = mapped_column(String(10), nullable=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant_vote: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    montant_reel: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    exercice: Mapped["ExerciceFinancier"] = relationship(
        "ExerciceFinancier", back_populates="recettes_investissement"
    )


class DepenseInvestissement(Base):
    __tablename__ = "depenses_investissement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exercice_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercices_financiers.id"), nullable=False)
    chapitre: Mapped[str] = mapped_column(String(10), nullable=False)
    article: Mapped[str | None] = mapped_column(String(10), nullable=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant_vote: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    montant_reel: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    exercice: Mapped["ExerciceFinancier"] = relationship(
        "ExerciceFinancier", back_populates="depenses_investissement"
    )
