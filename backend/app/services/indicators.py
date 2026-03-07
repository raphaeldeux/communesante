"""
Calcul des indicateurs de santé financière d'une commune.
"""
import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

# Définition des indicateurs avec leurs seuils d'alerte
INDICATEURS_DEF = {
    "epargne_brute": {
        "libelle": "Épargne brute",
        "unite": "€",
        "seuil_warning": None,  # calculé dynamiquement (% des recettes)
        "description": "Recettes réelles fonct. - Dépenses réelles fonct.",
    },
    "epargne_brute_pct": {
        "libelle": "Épargne brute (% recettes)",
        "unite": "%",
        "seuil_critical": Decimal("8"),
        "description": "Épargne brute / Recettes réelles fonctionnement",
    },
    "epargne_nette": {
        "libelle": "Épargne nette",
        "unite": "€",
        "description": "Épargne brute - Remboursement capital dette",
    },
    "epargne_nette_pct": {
        "libelle": "Épargne nette (% recettes)",
        "unite": "%",
        "seuil_critical": Decimal("2"),
        "description": "Épargne nette / Recettes réelles fonctionnement",
    },
    "capacite_desendettement": {
        "libelle": "Capacité de désendettement",
        "unite": "ans",
        "seuil_critical": Decimal("12"),
        "description": "Encours dette / Épargne brute",
    },
    "taux_rigidite": {
        "libelle": "Taux de rigidité des charges",
        "unite": "%",
        "seuil_warning": Decimal("60"),
        "seuil_critical": Decimal("65"),
        "description": "(Personnel + Dette) / Recettes réelles fonctionnement",
    },
    "taux_fonctionnement": {
        "libelle": "Taux de fonctionnement",
        "unite": "%",
        "seuil_warning": Decimal("90"),
        "seuil_critical": Decimal("95"),
        "description": "Dépenses réelles fonct. / Recettes réelles fonct.",
    },
    "effort_equipement": {
        "libelle": "Effort d'équipement",
        "unite": "%",
        "seuil_warning": Decimal("10"),  # < 10% = faible
        "description": "Dépenses équipement / Recettes fonctionnement",
    },
    "dependance_dgf": {
        "libelle": "Dépendance aux dotations (DGF)",
        "unite": "%",
        "seuil_warning": Decimal("25"),
        "description": "DGF / Recettes totales fonctionnement",
    },
    "total_recettes_fonctionnement": {
        "libelle": "Recettes de fonctionnement",
        "unite": "€",
    },
    "total_depenses_fonctionnement": {
        "libelle": "Dépenses de fonctionnement",
        "unite": "€",
    },
    "total_recettes_investissement": {
        "libelle": "Recettes d'investissement",
        "unite": "€",
    },
    "total_depenses_investissement": {
        "libelle": "Dépenses d'investissement",
        "unite": "€",
    },
    "charges_personnel": {
        "libelle": "Charges de personnel",
        "unite": "€",
    },
    "dotations_dgf": {
        "libelle": "Dotation Globale de Fonctionnement",
        "unite": "€",
    },
    "depenses_equipement": {
        "libelle": "Dépenses d'équipement",
        "unite": "€",
    },
    "remboursement_capital": {
        "libelle": "Remboursement capital dette",
        "unite": "€",
    },
    "interets_dette": {
        "libelle": "Intérêts de la dette",
        "unite": "€",
    },
}


def _sum_montant(lignes: list[Any], chapitre_prefix: str | None = None) -> Decimal:
    """Somme les montants réels d'un ensemble de lignes financières."""
    total = Decimal("0")
    for ligne in lignes:
        if chapitre_prefix and not ligne.chapitre.startswith(chapitre_prefix):
            continue
        val = ligne.montant_reel or ligne.montant_vote
        if val:
            total += Decimal(str(val))
    return total


def _sum_by_article_prefix(lignes: list[Any], article_prefix: str) -> Decimal:
    """Somme les montants pour les lignes dont l'article commence par un préfixe."""
    total = Decimal("0")
    for ligne in lignes:
        article = ligne.article or ""
        if article.startswith(article_prefix):
            val = ligne.montant_reel or ligne.montant_vote
            if val:
                total += Decimal(str(val))
    return total


def calculate_indicators(
    recettes_fonct: list[Any],
    depenses_fonct: list[Any],
    recettes_invest: list[Any],
    depenses_invest: list[Any],
) -> dict[str, Decimal | None]:
    """
    Calcule tous les indicateurs financiers à partir des données brutes.

    Returns:
        dict: code_indicateur -> valeur (Decimal)
    """
    results: dict[str, Decimal | None] = {}

    # Totaux de base
    total_recettes_fonct = _sum_montant(recettes_fonct)
    total_depenses_fonct = _sum_montant(depenses_fonct)
    total_recettes_invest = _sum_montant(recettes_invest)
    total_depenses_invest = _sum_montant(depenses_invest)

    results["total_recettes_fonctionnement"] = total_recettes_fonct
    results["total_depenses_fonctionnement"] = total_depenses_fonct
    results["total_recettes_investissement"] = total_recettes_invest
    results["total_depenses_investissement"] = total_depenses_invest

    # Charges de personnel (chapitre 012)
    charges_personnel = _sum_montant(depenses_fonct, chapitre_prefix="012")
    results["charges_personnel"] = charges_personnel

    # Intérêts de la dette (chapitre 66)
    interets_dette = _sum_montant(depenses_fonct, chapitre_prefix="66")
    results["interets_dette"] = interets_dette

    # Remboursement capital (chapitre 16 investissement, article 1641)
    remboursement_capital = _sum_montant(depenses_invest, chapitre_prefix="16")
    results["remboursement_capital"] = remboursement_capital

    # Dépenses d'équipement (chapitres 20, 21, 23)
    depenses_equipement = (
        _sum_montant(depenses_invest, chapitre_prefix="20")
        + _sum_montant(depenses_invest, chapitre_prefix="21")
        + _sum_montant(depenses_invest, chapitre_prefix="23")
    )
    results["depenses_equipement"] = depenses_equipement

    # DGF (chapitre 74, article 7411)
    dgf = Decimal("0")
    for ligne in recettes_fonct:
        if ligne.chapitre == "74" and (ligne.article or "").startswith("7411"):
            val = ligne.montant_reel or ligne.montant_vote
            if val:
                dgf += Decimal(str(val))
    results["dotations_dgf"] = dgf

    # Épargne brute = Recettes réelles fonct. - Dépenses réelles fonct.
    epargne_brute = total_recettes_fonct - total_depenses_fonct
    results["epargne_brute"] = epargne_brute

    # Épargne brute en % des recettes
    if total_recettes_fonct > 0:
        results["epargne_brute_pct"] = (epargne_brute / total_recettes_fonct * 100).quantize(Decimal("0.01"))
    else:
        results["epargne_brute_pct"] = None

    # Épargne nette = Épargne brute - Remboursement capital
    epargne_nette = epargne_brute - remboursement_capital
    results["epargne_nette"] = epargne_nette

    if total_recettes_fonct > 0:
        results["epargne_nette_pct"] = (epargne_nette / total_recettes_fonct * 100).quantize(Decimal("0.01"))
    else:
        results["epargne_nette_pct"] = None

    # Taux de rigidité = (Personnel + Intérêts dette) / Recettes fonct.
    if total_recettes_fonct > 0:
        taux_rigidite = ((charges_personnel + interets_dette) / total_recettes_fonct * 100).quantize(
            Decimal("0.01")
        )
        results["taux_rigidite"] = taux_rigidite
    else:
        results["taux_rigidite"] = None

    # Taux de fonctionnement = Dépenses fonct. / Recettes fonct.
    if total_recettes_fonct > 0:
        results["taux_fonctionnement"] = (
            total_depenses_fonct / total_recettes_fonct * 100
        ).quantize(Decimal("0.01"))
    else:
        results["taux_fonctionnement"] = None

    # Effort d'équipement = Dépenses équipement / Recettes fonct.
    if total_recettes_fonct > 0:
        results["effort_equipement"] = (
            depenses_equipement / total_recettes_fonct * 100
        ).quantize(Decimal("0.01"))
    else:
        results["effort_equipement"] = None

    # Dépendance DGF = DGF / Recettes totales fonct.
    if total_recettes_fonct > 0:
        results["dependance_dgf"] = (dgf / total_recettes_fonct * 100).quantize(Decimal("0.01"))
    else:
        results["dependance_dgf"] = None

    return results


def calculate_score(indicators: dict[str, Decimal | None]) -> tuple[int, list[dict]]:
    """
    Calcule le score global de santé financière (0-100) et les alertes.

    Returns:
        (score, alertes)
    """
    score = 100
    alertes = []

    def check(code: str, seuil_critical: float | None, seuil_warning: float | None,
               direction: str = "below_is_bad"):
        """
        direction: "below_is_bad" si une valeur basse est mauvaise,
                   "above_is_bad" si une valeur haute est mauvaise.
        """
        nonlocal score
        valeur = indicators.get(code)
        if valeur is None:
            return

        val_float = float(valeur)
        defn = INDICATEURS_DEF.get(code, {})

        if direction == "below_is_bad":
            if seuil_critical and val_float < seuil_critical:
                score -= 15
                alertes.append({
                    "indicateur": code,
                    "severite": "CRITICAL",
                    "message": f"{defn.get('libelle', code)}: {val_float:.1f}{defn.get('unite', '')} "
                               f"(seuil critique: {seuil_critical}{defn.get('unite', '')})",
                })
            elif seuil_warning and val_float < seuil_warning:
                score -= 8
                alertes.append({
                    "indicateur": code,
                    "severite": "WARNING",
                    "message": f"{defn.get('libelle', code)}: {val_float:.1f}{defn.get('unite', '')} "
                               f"(seuil d'alerte: {seuil_warning}{defn.get('unite', '')})",
                })
        else:  # above_is_bad
            if seuil_critical and val_float > seuil_critical:
                score -= 15
                alertes.append({
                    "indicateur": code,
                    "severite": "CRITICAL",
                    "message": f"{defn.get('libelle', code)}: {val_float:.1f}{defn.get('unite', '')} "
                               f"(seuil critique: {seuil_critical}{defn.get('unite', '')})",
                })
            elif seuil_warning and val_float > seuil_warning:
                score -= 8
                alertes.append({
                    "indicateur": code,
                    "severite": "WARNING",
                    "message": f"{defn.get('libelle', code)}: {val_float:.1f}{defn.get('unite', '')} "
                               f"(seuil d'alerte: {seuil_warning}{defn.get('unite', '')})",
                })

    # Évaluation des indicateurs
    check("epargne_brute_pct", seuil_critical=8.0, seuil_warning=None, direction="below_is_bad")
    check("epargne_nette_pct", seuil_critical=2.0, seuil_warning=None, direction="below_is_bad")
    check("capacite_desendettement", seuil_critical=12.0, seuil_warning=10.0, direction="above_is_bad")
    check("taux_rigidite", seuil_critical=65.0, seuil_warning=60.0, direction="above_is_bad")
    check("taux_fonctionnement", seuil_critical=95.0, seuil_warning=90.0, direction="above_is_bad")
    check("effort_equipement", seuil_critical=None, seuil_warning=10.0, direction="below_is_bad")
    check("dependance_dgf", seuil_critical=None, seuil_warning=25.0, direction="above_is_bad")

    score = max(0, min(100, score))
    return score, alertes


def get_score_interpretation(score: int) -> str:
    """Retourne l'interprétation textuelle du score."""
    if score >= 80:
        return "Santé financière excellente"
    elif score >= 65:
        return "Santé financière bonne"
    elif score >= 50:
        return "Santé financière correcte, vigilance recommandée"
    elif score >= 35:
        return "Santé financière préoccupante"
    else:
        return "Santé financière critique - action urgente requise"
