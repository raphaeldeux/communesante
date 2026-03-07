"""Routes pour les indicateurs et le score de santé financière."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.commune import Commune
from app.models.indicateur import Indicateur, Alerte
from app.schemas.indicateur import IndicateurSchema, AlerteSchema, ScoreSchema, KpiCard
from app.services.indicators import INDICATEURS_DEF, get_score_interpretation

router = APIRouter(prefix="/communes", tags=["Indicateurs"])


async def _get_commune_or_404(insee: str, db: AsyncSession) -> Commune:
    result = await db.execute(select(Commune).where(Commune.code_insee == insee))
    commune = result.scalar_one_or_none()
    if not commune:
        raise HTTPException(status_code=404, detail=f"Commune {insee} non trouvée")
    return commune


@router.get("/{insee}/indicateurs/{annee}", response_model=list[IndicateurSchema])
async def get_indicateurs(insee: str, annee: int, db: AsyncSession = Depends(get_db)):
    """Retourne les indicateurs calculés pour un exercice."""
    commune = await _get_commune_or_404(insee, db)
    result = await db.execute(
        select(Indicateur).where(
            Indicateur.commune_id == commune.id,
            Indicateur.annee == annee,
        )
    )
    return result.scalars().all()


@router.get("/{insee}/score", response_model=ScoreSchema)
async def get_score(insee: str, annee: int | None = None, db: AsyncSession = Depends(get_db)):
    """Retourne le score global de santé financière."""
    commune = await _get_commune_or_404(insee, db)

    # Trouver l'année la plus récente si non spécifiée
    if annee is None:
        result = await db.execute(
            select(Indicateur.annee)
            .where(Indicateur.commune_id == commune.id)
            .order_by(Indicateur.annee.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Aucune donnée disponible. Lancez une synchronisation.")
        annee = row

    # Récupérer tous les indicateurs
    result = await db.execute(
        select(Indicateur).where(
            Indicateur.commune_id == commune.id,
            Indicateur.annee == annee,
        )
    )
    indicateurs = {i.code_indicateur: i.valeur for i in result.scalars().all()}

    score_val = indicateurs.get("score_global")
    score = int(float(score_val)) if score_val else 0

    # Compter les alertes actives
    alertes_result = await db.execute(
        select(Alerte).where(
            Alerte.commune_id == commune.id,
            Alerte.annee == annee,
            Alerte.resolue == False,  # noqa: E712
        )
    )
    alertes = alertes_result.scalars().all()

    # Construire les KPIs principaux
    kpis_config = [
        ("epargne_brute_pct", "%", Decimal("8"), "below_is_bad"),
        ("epargne_nette_pct", "%", Decimal("2"), "below_is_bad"),
        ("taux_rigidite", "%", Decimal("65"), "above_is_bad"),
        ("taux_fonctionnement", "%", Decimal("95"), "above_is_bad"),
        ("capacite_desendettement", "ans", Decimal("12"), "above_is_bad"),
        ("effort_equipement", "%", Decimal("10"), "below_is_bad"),
    ]

    kpis = []
    for code, unite, seuil, direction in kpis_config:
        valeur = indicateurs.get(code)
        defn = INDICATEURS_DEF.get(code, {})

        # Calculer le statut
        statut = "ok"
        if valeur is not None:
            val_float = float(valeur)
            seuil_float = float(seuil)
            if direction == "below_is_bad" and val_float < seuil_float:
                statut = "critical"
            elif direction == "above_is_bad" and val_float > seuil_float:
                statut = "critical"

        kpis.append(KpiCard(
            code=code,
            libelle=defn.get("libelle", code),
            valeur=valeur,
            unite=defn.get("unite", unite),
            seuil_alerte=seuil,
            statut=statut,
            tendance=None,  # Calculé avec comparaison N-1
        ))

    return ScoreSchema(
        commune_id=commune.id,
        annee=annee,
        score=score,
        interpretation=get_score_interpretation(score),
        kpis=kpis,
        alertes_actives=len([a for a in alertes if not a.resolue]),
    )


@router.get("/{insee}/alertes", response_model=list[AlerteSchema])
async def get_alertes(
    insee: str,
    annee: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retourne les alertes actives pour une commune."""
    commune = await _get_commune_or_404(insee, db)

    query = select(Alerte).where(
        Alerte.commune_id == commune.id,
        Alerte.resolue == False,  # noqa: E712
    )
    if annee:
        query = query.where(Alerte.annee == annee)

    result = await db.execute(query.order_by(Alerte.annee.desc(), Alerte.severite))
    return result.scalars().all()


@router.get("/{insee}/evolution", response_model=list[dict])
async def get_evolution(insee: str, db: AsyncSession = Depends(get_db)):
    """Retourne l'évolution pluriannuelle des principaux indicateurs."""
    commune = await _get_commune_or_404(insee, db)

    codes_suivis = [
        "total_recettes_fonctionnement",
        "total_depenses_fonctionnement",
        "epargne_brute",
        "epargne_brute_pct",
        "taux_fonctionnement",
        "taux_rigidite",
        "score_global",
        "charges_personnel",
        "depenses_equipement",
    ]

    result = await db.execute(
        select(Indicateur).where(
            Indicateur.commune_id == commune.id,
            Indicateur.code_indicateur.in_(codes_suivis),
        ).order_by(Indicateur.annee)
    )
    indicateurs = result.scalars().all()

    # Regrouper par année
    evolution: dict[int, dict] = {}
    for indic in indicateurs:
        if indic.annee not in evolution:
            evolution[indic.annee] = {"annee": indic.annee}
        evolution[indic.annee][indic.code_indicateur] = float(indic.valeur) if indic.valeur else None

    return sorted(evolution.values(), key=lambda x: x["annee"])
