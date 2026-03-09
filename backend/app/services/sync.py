"""
Service de synchronisation des données financières depuis DGFiP.
"""
import logging
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.commune import Commune
from app.models.finance import (
    ExerciceFinancier,
    RecetteFonctionnement,
    DepenseFonctionnement,
    RecetteInvestissement,
    DepenseInvestissement,
    SourceDonnee,
    StatutExercice,
)
from app.models.indicateur import Indicateur, Alerte, Severite
from app.services.dgfip import fetch_finances_dgfip, get_commune_info
from app.services.indicators import calculate_indicators, calculate_score

logger = logging.getLogger(__name__)


async def get_or_create_commune(db: AsyncSession, code_insee: str) -> Commune:
    """Récupère ou crée une commune en base."""
    result = await db.execute(select(Commune).where(Commune.code_insee == code_insee))
    commune = result.scalar_one_or_none()

    if not commune:
        info = await get_commune_info(code_insee)
        commune = Commune(
            code_insee=code_insee,
            nom=info.get("nom", f"Commune {code_insee}") if info else f"Commune {code_insee}",
            population=info.get("population") if info else None,
            departement=info.get("departement") if info else None,
        )
        db.add(commune)
        await db.flush()
        logger.info(f"Commune créée: {commune.nom} ({code_insee})")

    return commune


async def sync_commune_finances(
    db: AsyncSession, code_insee: str, annees: list[int] | None = None
) -> dict:
    """
    Synchronise les données financières d'une commune pour les années spécifiées.

    Args:
        db: Session de base de données
        code_insee: Code INSEE de la commune
        annees: Liste des années à synchroniser (défaut: 2020-2024)

    Returns:
        Rapport de synchronisation
    """
    if annees is None:
        # L'OFGL publie les données N-1 au fil de l'année N.
        # Le dataset ofgl-base-communes-consolidee couvre actuellement 2017-2024.
        # On plafonne à 2024 pour éviter des requêtes sur des exercices non encore publiés.
        OFGL_LAST_YEAR = 2024
        annees = list(range(2020, OFGL_LAST_YEAR + 1))

    commune = await get_or_create_commune(db, code_insee)
    rapport = {"commune": commune.nom, "annees_traitees": [], "erreurs": []}

    for annee in annees:
        try:
            # Vérifier si l'exercice existe déjà
            result = await db.execute(
                select(ExerciceFinancier).where(
                    ExerciceFinancier.commune_id == commune.id,
                    ExerciceFinancier.annee == annee,
                )
            )
            exercice = result.scalar_one_or_none()

            if not exercice:
                exercice = ExerciceFinancier(
                    commune_id=commune.id,
                    annee=annee,
                    source=SourceDonnee.API,
                    statut=StatutExercice.BROUILLON,
                )
                db.add(exercice)
                await db.flush()

            # Récupérer les données DGFiP
            lignes = await fetch_finances_dgfip(code_insee, annee)
            if not lignes:
                rapport["erreurs"].append(f"Aucune donnée pour {annee}")
                continue

            # Supprimer les anciennes lignes
            for model in [
                RecetteFonctionnement, DepenseFonctionnement,
                RecetteInvestissement, DepenseInvestissement
            ]:
                result = await db.execute(
                    select(model).where(model.exercice_id == exercice.id)
                )
                for row in result.scalars().all():
                    await db.delete(row)

            # Insérer les nouvelles lignes
            for ligne in lignes:
                section = ligne.get("section")
                type_ligne = ligne.get("type")

                kwargs = {
                    "exercice_id": exercice.id,
                    "chapitre": ligne.get("chapitre", ""),
                    "article": ligne.get("article"),
                    "libelle": ligne.get("libelle", ""),
                    "montant_vote": Decimal(str(ligne.get("montant_vote", 0))),
                    "montant_reel": Decimal(str(ligne.get("montant_reel", 0))),
                }

                if section == "fonctionnement" and type_ligne == "recette":
                    db.add(RecetteFonctionnement(**kwargs))
                elif section == "fonctionnement" and type_ligne == "depense":
                    db.add(DepenseFonctionnement(**kwargs))
                elif section == "investissement" and type_ligne == "recette":
                    db.add(RecetteInvestissement(**kwargs))
                elif section == "investissement" and type_ligne == "depense":
                    db.add(DepenseInvestissement(**kwargs))

            exercice.statut = StatutExercice.SYNCHRONISE
            await db.flush()

            # Recalculer les indicateurs
            await recalculate_indicators(db, commune.id, annee, exercice.id)

            rapport["annees_traitees"].append(annee)
            logger.info(f"Synchronisation réussie: {commune.nom} / {annee}")

        except Exception as e:
            logger.error(f"Erreur synchronisation {code_insee}/{annee}: {e}")
            rapport["erreurs"].append(f"{annee}: {str(e)}")

    await db.commit()
    return rapport


async def recalculate_indicators(
    db: AsyncSession, commune_id: int, annee: int, exercice_id: int
) -> None:
    """Recalcule et sauvegarde les indicateurs pour un exercice."""
    # Charger les données
    recettes_fonct_result = await db.execute(
        select(RecetteFonctionnement).where(RecetteFonctionnement.exercice_id == exercice_id)
    )
    depenses_fonct_result = await db.execute(
        select(DepenseFonctionnement).where(DepenseFonctionnement.exercice_id == exercice_id)
    )
    recettes_invest_result = await db.execute(
        select(RecetteInvestissement).where(RecetteInvestissement.exercice_id == exercice_id)
    )
    depenses_invest_result = await db.execute(
        select(DepenseInvestissement).where(DepenseInvestissement.exercice_id == exercice_id)
    )

    recettes_fonct = recettes_fonct_result.scalars().all()
    depenses_fonct = depenses_fonct_result.scalars().all()
    recettes_invest = recettes_invest_result.scalars().all()
    depenses_invest = depenses_invest_result.scalars().all()

    # Calculer
    indicators = calculate_indicators(recettes_fonct, depenses_fonct, recettes_invest, depenses_invest)

    # Supprimer les anciens indicateurs
    old_indics = await db.execute(
        select(Indicateur).where(
            Indicateur.commune_id == commune_id, Indicateur.annee == annee
        )
    )
    for indic in old_indics.scalars().all():
        await db.delete(indic)

    # Sauvegarder les nouveaux indicateurs
    for code, valeur in indicators.items():
        db.add(Indicateur(
            commune_id=commune_id,
            annee=annee,
            code_indicateur=code,
            valeur=valeur,
        ))

    # Calculer et sauvegarder les alertes
    score, alertes_data = calculate_score(indicators)

    # Supprimer les anciennes alertes
    old_alertes = await db.execute(
        select(Alerte).where(
            Alerte.commune_id == commune_id, Alerte.annee == annee
        )
    )
    for alerte in old_alertes.scalars().all():
        await db.delete(alerte)

    # Sauvegarder les nouvelles alertes
    for alerte_data in alertes_data:
        db.add(Alerte(
            commune_id=commune_id,
            annee=annee,
            indicateur=alerte_data["indicateur"],
            severite=Severite(alerte_data["severite"]),
            message=alerte_data["message"],
        ))

    # Sauvegarder le score global
    db.add(Indicateur(
        commune_id=commune_id,
        annee=annee,
        code_indicateur="score_global",
        valeur=Decimal(str(score)),
    ))

    await db.flush()
