"""
Parser PDF pour les budgets primitifs des communes.
Extrait les tableaux financiers depuis les documents BP.
"""
import logging
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pdfplumber non disponible - import PDF désactivé")


def parse_montant(text: str) -> Decimal | None:
    """Convertit une chaîne de caractères en montant décimal."""
    if not text:
        return None
    # Nettoyer: supprimer espaces, remplacer virgule par point
    clean = re.sub(r"[^\d,.-]", "", text.strip())
    clean = clean.replace(",", ".").replace(" ", "")
    try:
        return Decimal(clean)
    except InvalidOperation:
        return None


def detect_section(text: str) -> str | None:
    """Détecte la section budgétaire (fonctionnement/investissement)."""
    text_lower = text.lower()
    if "fonctionnement" in text_lower:
        return "fonctionnement"
    if "investissement" in text_lower:
        return "investissement"
    return None


def detect_type(text: str) -> str | None:
    """Détecte le type de ligne (recette/dépense)."""
    text_lower = text.lower()
    if any(word in text_lower for word in ["recette", "produit", "ressource"]):
        return "recette"
    if any(word in text_lower for word in ["dépense", "charge", "emploi"]):
        return "depense"
    return None


def extract_chapitre_article(text: str) -> tuple[str, str | None]:
    """Extrait le chapitre et l'article depuis un code budgétaire."""
    # Format: 6141, 7411, etc.
    match = re.match(r"^(\d{2,3})(\d*)$", text.strip())
    if match:
        chapitre = match.group(1)
        article_suffix = match.group(2)
        article = text.strip() if article_suffix else None
        return chapitre, article
    return text.strip(), None


def parse_budget_pdf(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Parse un fichier PDF de budget primitif communal.

    Args:
        file_path: Chemin vers le fichier PDF

    Returns:
        Liste de dictionnaires représentant les lignes budgétaires
    """
    if not PDF_AVAILABLE:
        raise RuntimeError("pdfplumber n'est pas installé")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

    lignes = []
    current_section = None
    current_type = None

    with pdfplumber.open(str(file_path)) as pdf:
        logger.info(f"Parsing PDF: {file_path.name} ({len(pdf.pages)} pages)")

        for page_num, page in enumerate(pdf.pages, 1):
            # Essayer d'extraire les tableaux
            tables = page.extract_tables()

            if tables:
                for table in tables:
                    for row in table:
                        if not row or all(cell is None for cell in row):
                            continue

                        # Détecter la section dans les en-têtes
                        row_text = " ".join(str(c) for c in row if c)
                        section = detect_section(row_text)
                        if section:
                            current_section = section
                        type_ligne = detect_type(row_text)
                        if type_ligne:
                            current_type = type_ligne

                        # Chercher les lignes avec un code budgétaire et un montant
                        if len(row) >= 3:
                            code = str(row[0] or "").strip()
                            libelle = str(row[1] or "").strip()

                            # Chercher un montant dans les dernières colonnes
                            montant_vote = None
                            montant_reel = None

                            for i in range(len(row) - 1, 1, -1):
                                if row[i] and montant_vote is None:
                                    montant_vote = parse_montant(str(row[i]))
                                elif row[i] and montant_reel is None:
                                    montant_reel = parse_montant(str(row[i]))
                                if montant_vote and montant_reel:
                                    break

                            # Valider que le code ressemble à un code budgétaire
                            if re.match(r"^\d{2,6}$", code) and libelle and montant_vote:
                                chapitre, article = extract_chapitre_article(code)
                                lignes.append({
                                    "section": current_section or "fonctionnement",
                                    "type": current_type or "recette",
                                    "chapitre": chapitre,
                                    "article": article,
                                    "libelle": libelle[:255],
                                    "montant_vote": float(montant_vote) if montant_vote else None,
                                    "montant_reel": float(montant_reel) if montant_reel else None,
                                })

            else:
                # Fallback: extraction texte
                text = page.extract_text()
                if text:
                    lignes.extend(_parse_text_fallback(text, current_section, current_type))

    logger.info(f"Extraction PDF: {len(lignes)} lignes trouvées")
    return lignes


def _parse_text_fallback(text: str, current_section: str | None, current_type: str | None) -> list[dict]:
    """Extraction depuis le texte brut (fallback si pas de tableau détecté)."""
    lignes = []
    lines = text.split("\n")

    for line in lines:
        # Détecter les changements de section/type
        section = detect_section(line)
        if section:
            current_section = section
        type_ligne = detect_type(line)
        if type_ligne:
            current_type = type_ligne

        # Format typique: "6141  Sous-traitances générales  125 000"
        match = re.match(r"^(\d{2,6})\s+(.+?)\s+([\d\s.,]+)$", line.strip())
        if match:
            code = match.group(1)
            libelle = match.group(2).strip()
            montant_str = match.group(3).strip()
            montant = parse_montant(montant_str)

            if montant and montant > 0:
                chapitre, article = extract_chapitre_article(code)
                lignes.append({
                    "section": current_section or "fonctionnement",
                    "type": current_type or "recette",
                    "chapitre": chapitre,
                    "article": article,
                    "libelle": libelle[:255],
                    "montant_vote": float(montant),
                    "montant_reel": None,
                })

    return lignes
