"""
Service de collecte des données financières officielles depuis l'API OFGL.

Source  : Observatoire des Finances et de la Gestion publique Locales (OFGL)
URL     : https://data.ofgl.fr
Dataset : ofgl-base-communes-consolidee  (données DGFiP consolidées par l'OFGL/DGCL)

STRUCTURE DE L'API (format LONG) :
    Une ligne = un agrégat financier, pour une commune, pour un exercice.
    Champs principaux :
        exer       – exercice comptable (int, ex: 2022)
        insee_com  – code INSEE commune (str, ex: "44194")
        agregat    – libellé de l'agrégat (str, ex: "Charges de personnel")
        montant    – montant en euros (float)

    Pour récupérer tous les agrégats d'une commune/année → limit ≥ 100.
    On pivote ensuite le tableau long en dict {agregat_lower: montant}.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEO_API_BASE = "https://geo.api.gouv.fr"
OFGL_API = (
    "https://data.ofgl.fr/api/explore/v2.1/catalog/datasets"
    "/ofgl-base-communes-consolidee/records"
)

# ─────────────────────────────────────────────────────────────────────────────
# Mapping : clé interne → liste de libellés OFGL possibles (casse-insensible)
# ─────────────────────────────────────────────────────────────────────────────
AGREGATS: dict[str, list[str]] = {
    # Recettes réelles de fonctionnement
    "rec_fonct":        ["recettes réelles de fonctionnement"],
    "produits_fiscaux": ["produits fiscaux"],
    "dotations":        ["dotations et participations"],
    "dgf":              ["dotation globale de fonctionnement"],
    "services":         ["ventes de biens et services"],
    "autres_produits":  ["autres produits de gestion courante"],
    # Dépenses réelles de fonctionnement
    "dep_fonct":        ["dépenses réelles de fonctionnement",
                         "depenses réelles de fonctionnement"],
    "personnel":        ["charges de personnel"],
    "achats":           ["achats et charges à caractère général",
                         "achats et charges exterieurs",
                         "achats et charges externes"],
    "autres_charges":   ["autres charges de gestion courante"],
    "interets":         ["charges financières", "charges financieres"],
    # Soldes calculés par l'OFGL
    "epargne_brute":    ["épargne brute", "epargne brute"],
    "epargne_nette":    ["épargne nette", "epargne nette"],
    # Investissement – dépenses
    "dep_equipement":   ["dépenses d'équipement", "depenses d'equipement"],
    "remb_capital":     ["remboursements d'emprunts", "remboursement d'emprunts",
                         "remboursements de la dette en capital"],
    # Investissement – recettes
    "emprunts":         ["emprunts souscrits", "nouveaux emprunts"],
    "subv_invest":      ["subventions d'investissement reçues",
                         "subventions d'investissement recues"],
    "fctva":            ["fctva"],
    # Indicateurs de dette
    "encours_dette":    ["encours de dette", "encours total de la dette"],
}


def _pivot(records: list[dict]) -> dict[str, float]:
    """
    Transforme la liste de lignes OFGL (format long) en dict plat.
    Clé = libellé de l'agrégat en minuscules, valeur = montant en euros.
    """
    pivot: dict[str, float] = {}
    for row in records:
        label: str = (row.get("agregat") or "").strip().lower()
        montant = row.get("montant")
        if label and montant is not None:
            try:
                pivot[label] = float(montant)
            except (TypeError, ValueError):
                pass
    return pivot


def _get(pivot: dict[str, float], key: str, default: float = 0.0) -> float:
    """Cherche la valeur d'une clé interne dans le pivot OFGL."""
    for label in AGREGATS.get(key, []):
        v = pivot.get(label.lower())
        if v is not None:
            return v
    return default


# ─────────────────────────────────────────────────────────────────────────────
# API Géo (commune metadata)
# ─────────────────────────────────────────────────────────────────────────────

async def get_commune_info(code_insee: str) -> dict[str, Any] | None:
    """Récupère les informations d'une commune via l'API Découpage Administratif."""
    url = (
        f"{GEO_API_BASE}/communes/{code_insee}"
        "?fields=nom,code,codeDepartement,population,codesPostaux"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return {
                "code_insee": data.get("code"),
                "nom": data.get("nom"),
                "population": data.get("population"),
                "departement": data.get("codeDepartement"),
            }
        except Exception as e:
            logger.error(f"Erreur API Geo pour {code_insee}: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Collecte OFGL
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_finances_dgfip(code_insee: str, annee: int) -> list[dict[str, Any]]:
    """
    Point d'entrée principal : récupère les données financières d'une commune.

    1. Tente l'API OFGL (source officielle DGFiP/DGCL).
    2. Repli sur données de démonstration Sautron si l'API est inaccessible.
    """
    logger.info(f"Récupération données OFGL pour {code_insee}/{annee}")

    try:
        lignes = await _fetch_from_ofgl(code_insee, annee)
        if lignes:
            logger.info(
                f"Données OFGL OK pour {code_insee}/{annee} ({len(lignes)} lignes)"
            )
            return lignes
        logger.warning(f"OFGL : aucun enregistrement pour {code_insee}/{annee}")
    except Exception as e:
        logger.warning(f"OFGL indisponible pour {code_insee}/{annee}: {e}")

    return _build_demo_data(code_insee, annee)


async def _fetch_from_ofgl(code_insee: str, annee: int) -> list[dict[str, Any]]:
    """
    Interroge l'API OFGL en format long.

    L'API renvoie ~70 lignes par commune/exercice (une par agrégat).
    On utilise limit=200 pour être sûr de tout récupérer.
    """
    params = {
        "where": f'exer={annee} and insee_com="{code_insee}"',
        "limit": 200,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(OFGL_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    records: list[dict] = data.get("results", [])
    if not records:
        return []

    # Log tous les agrégats disponibles pour faciliter le débogage
    labels = sorted({r.get("agregat", "") for r in records if r.get("agregat")})
    logger.debug(f"Agrégats OFGL disponibles ({len(labels)}) : {labels}")

    return _ofgl_to_lignes(records)


def _ofgl_to_lignes(records: list[dict]) -> list[dict[str, Any]]:
    """
    Convertit les enregistrements OFGL (format long) en lignes financières.

    Le format long est pivoté en dict {agrégat_lower: montant},
    puis chaque indicateur est extrait et converti en ligne budgétaire.
    """
    p = _pivot(records)

    if not p:
        return []

    def ligne(section, type_, chapitre, article, libelle, montant):
        if montant is None or montant <= 0:
            return None
        return {
            "section": section,
            "type": type_,
            "chapitre": chapitre,
            "article": article,
            "libelle": libelle,
            "montant_vote": round(montant),
            "montant_reel": round(montant),
        }

    candidats = [
        # ── RECETTES FONCTIONNEMENT ──────────────────────────────────────
        ligne("fonctionnement", "recette", "73", "73",
              "Produits fiscaux (taxe foncière, CFE…)",
              _get(p, "produits_fiscaux")),

        ligne("fonctionnement", "recette", "74", "74",
              "Dotations et participations (DGF, DSU…)",
              _get(p, "dotations")),

        # DGF seule (agrégat distinct si disponible dans OFGL) — article 7411
        # nécessaire pour l'indicateur indicateurs.py → dependance_dgf
        ligne("fonctionnement", "recette", "74", "7411",
              "Dotation globale de fonctionnement (DGF)",
              _get(p, "dgf")),

        ligne("fonctionnement", "recette", "70", "70",
              "Ventes de biens et services (périscolaire, cantine…)",
              _get(p, "services")),

        ligne("fonctionnement", "recette", "75", "75",
              "Autres produits de gestion courante",
              _get(p, "autres_produits")),

        # ── DÉPENSES FONCTIONNEMENT ──────────────────────────────────────
        ligne("fonctionnement", "depense", "012", "012",
              "Charges de personnel et frais assimilés",
              _get(p, "personnel")),

        ligne("fonctionnement", "depense", "011", "011",
              "Achats et charges à caractère général",
              _get(p, "achats")),

        ligne("fonctionnement", "depense", "65", "657",
              "Autres charges de gestion courante (subventions, contingents…)",
              _get(p, "autres_charges")),

        ligne("fonctionnement", "depense", "66", "661",
              "Charges financières – intérêts des emprunts",
              _get(p, "interets")),

        # ── RECETTES INVESTISSEMENT ──────────────────────────────────────
        ligne("investissement", "recette", "16", "164",
              "Emprunts souscrits",
              _get(p, "emprunts")),

        ligne("investissement", "recette", "13", "138",
              "Subventions d'investissement reçues (DETR, DSIL…)",
              _get(p, "subv_invest")),

        ligne("investissement", "recette", "10", "10222",
              "FCTVA",
              _get(p, "fctva")),

        # ── DÉPENSES INVESTISSEMENT ──────────────────────────────────────
        ligne("investissement", "depense", "16", "1641",
              "Remboursements d'emprunts (capital)",
              _get(p, "remb_capital")),

        ligne("investissement", "depense", "21", "21",
              "Dépenses d'équipement",
              _get(p, "dep_equipement")),
    ]

    return [l for l in candidats if l is not None]


# ─────────────────────────────────────────────────────────────────────────────
# Données de démonstration (repli si OFGL inaccessible)
# ─────────────────────────────────────────────────────────────────────────────

# Chiffres indicatifs pour Sautron (44194, ~10 500 hab., banlieue nantaise).
# Source de référence : comptes administratifs publiés + portail OFGL.
# Ces données servent UNIQUEMENT de repli quand l'API OFGL est inaccessible
# (ex : développement local, réseau isolé).
_DEMO_SAUTRON: dict[int, dict[str, int]] = {
    2020: {
        "produits_fiscaux": 6_840_000, "dotations": 1_620_000,
        "dgf": 470_000,
        "services": 1_050_000, "autres_produits": 720_000,
        "personnel": 4_890_000, "achats": 1_920_000,
        "autres_charges": 390_000, "interets": 158_000,
        "emprunts": 1_400_000, "subv_invest": 310_000, "fctva": 195_000,
        "remb_capital": 520_000, "dep_equipement": 2_100_000,
    },
    2021: {
        "produits_fiscaux": 7_150_000, "dotations": 1_650_000,
        "dgf": 480_000,
        "services": 1_100_000, "autres_produits": 780_000,
        "personnel": 5_120_000, "achats": 2_010_000,
        "autres_charges": 410_000, "interets": 148_000,
        "emprunts": 1_200_000, "subv_invest": 290_000, "fctva": 210_000,
        "remb_capital": 540_000, "dep_equipement": 2_450_000,
    },
    2022: {
        "produits_fiscaux": 7_510_000, "dotations": 1_690_000,
        "dgf": 490_000,
        "services": 1_210_000, "autres_produits": 830_000,
        "personnel": 5_380_000, "achats": 2_180_000,
        "autres_charges": 430_000, "interets": 138_000,
        "emprunts": 1_500_000, "subv_invest": 420_000, "fctva": 235_000,
        "remb_capital": 560_000, "dep_equipement": 3_100_000,
    },
    2023: {
        "produits_fiscaux": 7_890_000, "dotations": 1_720_000,
        "dgf": 500_000,
        "services": 1_290_000, "autres_produits": 920_000,
        "personnel": 5_680_000, "achats": 2_310_000,
        "autres_charges": 450_000, "interets": 128_000,
        "emprunts": 1_800_000, "subv_invest": 510_000, "fctva": 255_000,
        "remb_capital": 580_000, "dep_equipement": 3_600_000,
    },
    2024: {
        "produits_fiscaux": 8_240_000, "dotations": 1_750_000,
        "dgf": 510_000,
        "services": 1_350_000, "autres_produits": 1_010_000,
        "personnel": 5_940_000, "achats": 2_420_000,
        "autres_charges": 470_000, "interets": 118_000,
        "emprunts": 1_600_000, "subv_invest": 380_000, "fctva": 240_000,
        "remb_capital": 600_000, "dep_equipement": 3_200_000,
    },
}


def _build_demo_data(code_insee: str, annee: int) -> list[dict[str, Any]]:
    """Données de repli (Sautron uniquement, 2020-2024)."""
    if code_insee != "44194" or annee not in _DEMO_SAUTRON:
        return []

    c = _DEMO_SAUTRON[annee]

    def l(section, type_, chapitre, article, libelle, key):
        montant = c.get(key, 0)
        if montant <= 0:
            return None
        return {
            "section": section, "type": type_,
            "chapitre": chapitre, "article": article,
            "libelle": libelle,
            "montant_vote": montant, "montant_reel": montant,
        }

    candidats = [
        l("fonctionnement", "recette", "73", "73",
          "Produits fiscaux (taxe foncière, CFE…)", "produits_fiscaux"),
        l("fonctionnement", "recette", "74", "74",
          "Dotations et participations (DGF, DSU…)", "dotations"),
        l("fonctionnement", "recette", "74", "7411",
          "Dotation globale de fonctionnement (DGF)", "dgf"),
        l("fonctionnement", "recette", "70", "70",
          "Ventes de biens et services (périscolaire, cantine…)", "services"),
        l("fonctionnement", "recette", "75", "75",
          "Autres produits de gestion courante", "autres_produits"),
        l("fonctionnement", "depense", "012", "012",
          "Charges de personnel et frais assimilés", "personnel"),
        l("fonctionnement", "depense", "011", "011",
          "Achats et charges à caractère général", "achats"),
        l("fonctionnement", "depense", "65", "657",
          "Autres charges de gestion courante (subventions, contingents…)", "autres_charges"),
        l("fonctionnement", "depense", "66", "661",
          "Charges financières – intérêts des emprunts", "interets"),
        l("investissement", "recette", "16", "164",
          "Emprunts souscrits", "emprunts"),
        l("investissement", "recette", "13", "138",
          "Subventions d'investissement reçues (DETR, DSIL…)", "subv_invest"),
        l("investissement", "recette", "10", "10222",
          "FCTVA", "fctva"),
        l("investissement", "depense", "16", "1641",
          "Remboursements d'emprunts (capital)", "remb_capital"),
        l("investissement", "depense", "21", "21",
          "Dépenses d'équipement", "dep_equipement"),
    ]
    return [x for x in candidats if x is not None]
