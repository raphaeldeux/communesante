"""Dépendances FastAPI réutilisables."""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)


async def verify_token(api_key: str | None = Security(api_key_header)) -> str:
    """Vérifie le token API dans l'en-tête X-API-Token."""
    if api_key == settings.api_secret_token:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token API invalide ou manquant",
    )
