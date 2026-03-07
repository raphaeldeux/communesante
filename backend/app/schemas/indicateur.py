from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.models.indicateur import Severite


class IndicateurSchema(BaseModel):
    id: int
    commune_id: int
    annee: int
    code_indicateur: str
    valeur: Decimal | None
    date_calcul: datetime

    model_config = {"from_attributes": True}


class AlerteSchema(BaseModel):
    id: int
    commune_id: int
    annee: int
    indicateur: str
    severite: Severite
    message: str
    resolue: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KpiCard(BaseModel):
    code: str
    libelle: str
    valeur: Decimal | None
    unite: str
    seuil_alerte: Decimal | None
    statut: str  # "ok", "warning", "critical"
    tendance: str | None  # "hausse", "baisse", "stable"


class ScoreSchema(BaseModel):
    commune_id: int
    annee: int
    score: int  # /100
    interpretation: str
    kpis: list[KpiCard]
    alertes_actives: int
