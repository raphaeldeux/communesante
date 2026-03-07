from datetime import datetime
from pydantic import BaseModel


class CommuneCreate(BaseModel):
    code_insee: str
    siret: str | None = None
    nom: str
    population: int | None = None
    departement: str | None = None


class CommuneSchema(BaseModel):
    id: int
    code_insee: str
    siret: str | None
    nom: str
    population: int | None
    departement: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
