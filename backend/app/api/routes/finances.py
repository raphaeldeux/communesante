"""Routes pour les données financières."""
import os
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
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
from app.schemas.finance import ExerciceFinancierSchema, FinancesDetailSchema, LigneFinanciereSchema
from app.services.sync import sync_commune_finances, recalculate_indicators, get_or_create_commune

router = APIRouter(prefix="/communes", tags=["Finances"])


async def _get_commune_or_404(insee: str, db: AsyncSession) -> Commune:
    result = await db.execute(select(Commune).where(Commune.code_insee == insee))
    commune = result.scalar_one_or_none()
    if not commune:
        raise HTTPException(status_code=404, detail=f"Commune {insee} non trouvée. Lancez une synchronisation d'abord.")
    return commune


@router.get("/{insee}/finances", response_model=list[ExerciceFinancierSchema])
async def get_all_finances(insee: str, db: AsyncSession = Depends(get_db)):
    """Retourne la liste des exercices financiers disponibles pour une commune."""
    commune = await _get_commune_or_404(insee, db)
    result = await db.execute(
        select(ExerciceFinancier)
        .where(ExerciceFinancier.commune_id == commune.id)
        .order_by(ExerciceFinancier.annee.desc())
    )
    return result.scalars().all()


@router.get("/{insee}/finances/{annee}", response_model=FinancesDetailSchema)
async def get_finances_annee(insee: str, annee: int, db: AsyncSession = Depends(get_db)):
    """Retourne le détail des données financières pour une année."""
    commune = await _get_commune_or_404(insee, db)

    result = await db.execute(
        select(ExerciceFinancier).where(
            ExerciceFinancier.commune_id == commune.id,
            ExerciceFinancier.annee == annee,
        )
    )
    exercice = result.scalar_one_or_none()
    if not exercice:
        raise HTTPException(status_code=404, detail=f"Pas de données pour {annee}")

    # Charger toutes les lignes
    rf = (await db.execute(select(RecetteFonctionnement).where(RecetteFonctionnement.exercice_id == exercice.id))).scalars().all()
    df = (await db.execute(select(DepenseFonctionnement).where(DepenseFonctionnement.exercice_id == exercice.id))).scalars().all()
    ri = (await db.execute(select(RecetteInvestissement).where(RecetteInvestissement.exercice_id == exercice.id))).scalars().all()
    di = (await db.execute(select(DepenseInvestissement).where(DepenseInvestissement.exercice_id == exercice.id))).scalars().all()

    def total(lignes):
        return sum((Decimal(str(l.montant_reel or l.montant_vote or 0)) for l in lignes), Decimal("0"))

    total_rf = total(rf)
    total_df = total(df)
    epargne_brute = total_rf - total_df

    return FinancesDetailSchema(
        exercice=ExerciceFinancierSchema.model_validate(exercice),
        recettes_fonctionnement=[LigneFinanciereSchema.model_validate(l) for l in rf],
        depenses_fonctionnement=[LigneFinanciereSchema.model_validate(l) for l in df],
        recettes_investissement=[LigneFinanciereSchema.model_validate(l) for l in ri],
        depenses_investissement=[LigneFinanciereSchema.model_validate(l) for l in di],
        total_recettes_fonctionnement=total_rf,
        total_depenses_fonctionnement=total_df,
        total_recettes_investissement=total(ri),
        total_depenses_investissement=total(di),
        epargne_brute=epargne_brute,
    )


@router.post("/{insee}/sync")
async def sync_finances(
    insee: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Déclenche une synchronisation avec l'API DGFiP en arrière-plan."""
    # Créer la commune si elle n'existe pas
    await get_or_create_commune(db, insee)
    await db.commit()

    background_tasks.add_task(_run_sync, insee)
    return {"message": f"Synchronisation déclenchée pour {insee}", "status": "pending"}


async def _run_sync(insee: str):
    """Tâche de synchronisation en arrière-plan."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            rapport = await sync_commune_finances(db, insee)
            import logging
            logging.getLogger(__name__).info(f"Sync terminée: {rapport}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur sync {insee}: {e}")


@router.post("/{insee}/import-pdf")
async def import_pdf(
    insee: str,
    annee: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload et parsing d'un fichier PDF de budget primitif."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    commune = await get_or_create_commune(db, insee)
    await db.flush()

    # Sauvegarder le fichier
    upload_dir = os.path.join(settings.uploads_dir, insee)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{annee}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Parser le PDF
    try:
        from app.parsers.pdf_parser import parse_budget_pdf
        lignes = parse_budget_pdf(filepath)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erreur parsing PDF: {str(e)}")

    if not lignes:
        raise HTTPException(status_code=422, detail="Aucune donnée financière trouvée dans le PDF")

    # Créer ou mettre à jour l'exercice
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
            source=SourceDonnee.PDF,
            statut=StatutExercice.BROUILLON,
            fichier_pdf=filepath,
        )
        db.add(exercice)
        await db.flush()

    # Supprimer les anciennes lignes
    for model in [RecetteFonctionnement, DepenseFonctionnement, RecetteInvestissement, DepenseInvestissement]:
        old = (await db.execute(select(model).where(model.exercice_id == exercice.id))).scalars().all()
        for row in old:
            await db.delete(row)

    # Insérer les nouvelles lignes
    nb_lignes = 0
    for ligne in lignes:
        section = ligne.get("section", "fonctionnement")
        type_ligne = ligne.get("type", "recette")
        kwargs = {
            "exercice_id": exercice.id,
            "chapitre": ligne.get("chapitre", ""),
            "article": ligne.get("article"),
            "libelle": ligne.get("libelle", ""),
            "montant_vote": Decimal(str(ligne.get("montant_vote") or 0)),
            "montant_reel": Decimal(str(ligne.get("montant_reel") or 0)) if ligne.get("montant_reel") else None,
        }

        if section == "fonctionnement" and type_ligne == "recette":
            db.add(RecetteFonctionnement(**kwargs))
        elif section == "fonctionnement" and type_ligne == "depense":
            db.add(DepenseFonctionnement(**kwargs))
        elif section == "investissement" and type_ligne == "recette":
            db.add(RecetteInvestissement(**kwargs))
        elif section == "investissement" and type_ligne == "depense":
            db.add(DepenseInvestissement(**kwargs))
        nb_lignes += 1

    exercice.statut = StatutExercice.VALIDE
    exercice.source = SourceDonnee.PDF
    await db.flush()

    # Recalculer les indicateurs
    await recalculate_indicators(db, commune.id, annee, exercice.id)
    await db.commit()

    return {
        "message": f"Import réussi: {nb_lignes} lignes importées",
        "annee": annee,
        "lignes": nb_lignes,
        "fichier": filename,
    }
