from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.models.finance import SourceDonnee, StatutExercice


class LigneFinanciereSchema(BaseModel):
    id: int
    chapitre: str
    article: str | None
    libelle: str
    montant_vote: Decimal | None
    montant_reel: Decimal | None

    model_config = {"from_attributes": True}


class ExerciceFinancierSchema(BaseModel):
    id: int
    commune_id: int
    annee: int
    source: SourceDonnee
    statut: StatutExercice
    fichier_pdf: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FinancesDetailSchema(BaseModel):
    exercice: ExerciceFinancierSchema
    recettes_fonctionnement: list[LigneFinanciereSchema]
    depenses_fonctionnement: list[LigneFinanciereSchema]
    recettes_investissement: list[LigneFinanciereSchema]
    depenses_investissement: list[LigneFinanciereSchema]

    # Agrégats calculés
    total_recettes_fonctionnement: Decimal
    total_depenses_fonctionnement: Decimal
    total_recettes_investissement: Decimal
    total_depenses_investissement: Decimal
    epargne_brute: Decimal
