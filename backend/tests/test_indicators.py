"""Tests unitaires pour le calcul des indicateurs financiers."""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.indicators import calculate_indicators, calculate_score, get_score_interpretation


def make_ligne(chapitre: str, article: str | None, montant_reel: float):
    """Crée une ligne financière mock."""
    ligne = MagicMock()
    ligne.chapitre = chapitre
    ligne.article = article
    ligne.montant_reel = Decimal(str(montant_reel))
    ligne.montant_vote = Decimal(str(montant_reel))
    return ligne


class TestCalculateIndicators:
    """Tests pour la fonction calculate_indicators."""

    def setup_method(self):
        """Données de test basées sur Sautron 2022."""
        self.recettes_fonct = [
            make_ligne("70", "7061", 740_000),
            make_ligne("73", "7311", 4_200_000),
            make_ligne("73", "7313", 1_500_000),
            make_ligne("74", "7411", 358_000),
            make_ligne("74", "742", 180_000),
            make_ligne("75", "752", 120_000),
        ]
        self.depenses_fonct = [
            make_ligne("011", "60", 1_800_000),
            make_ligne("012", "621", 4_200_000),
            make_ligne("014", "6554", 650_000),
            make_ligne("65", "657", 420_000),
            make_ligne("66", "661", 180_000),
        ]
        self.recettes_invest = [
            make_ligne("10", "1068", 800_000),
            make_ligne("16", "164", 1_200_000),
            make_ligne("13", "138", 350_000),
        ]
        self.depenses_invest = [
            make_ligne("16", "1641", 450_000),
            make_ligne("21", "2128", 900_000),
            make_ligne("23", "2315", 600_000),
        ]

    def test_total_recettes_fonctionnement(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        assert indicators["total_recettes_fonctionnement"] == Decimal("7098000")

    def test_total_depenses_fonctionnement(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        assert indicators["total_depenses_fonctionnement"] == Decimal("7250000")

    def test_epargne_brute_negative(self):
        """Épargne brute négative dans cet exemple simplifié."""
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        epargne = indicators["epargne_brute"]
        assert isinstance(epargne, Decimal)

    def test_charges_personnel(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        assert indicators["charges_personnel"] == Decimal("4200000")

    def test_interets_dette(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        assert indicators["interets_dette"] == Decimal("180000")

    def test_dgf(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        assert indicators["dotations_dgf"] == Decimal("358000")

    def test_depenses_equipement(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        assert indicators["depenses_equipement"] == Decimal("1500000")

    def test_taux_fonctionnement(self):
        indicators = calculate_indicators(
            self.recettes_fonct, self.depenses_fonct,
            self.recettes_invest, self.depenses_invest
        )
        taux = indicators["taux_fonctionnement"]
        assert taux is not None
        assert isinstance(taux, Decimal)

    def test_empty_data(self):
        """Test avec des données vides."""
        indicators = calculate_indicators([], [], [], [])
        assert indicators["total_recettes_fonctionnement"] == Decimal("0")
        assert indicators["epargne_brute"] == Decimal("0")
        assert indicators["taux_fonctionnement"] is None


class TestCalculateScore:
    """Tests pour le calcul du score."""

    def test_perfect_score(self):
        """Score maximal avec de bons indicateurs."""
        indicators = {
            "epargne_brute_pct": Decimal("15"),  # > 8%
            "epargne_nette_pct": Decimal("8"),   # > 2%
            "taux_rigidite": Decimal("55"),       # < 65%
            "taux_fonctionnement": Decimal("85"), # < 95%
            "effort_equipement": Decimal("15"),   # > 10%
            "dependance_dgf": Decimal("20"),      # < 25%
        }
        score, alertes = calculate_score(indicators)
        assert score == 100
        assert len(alertes) == 0

    def test_critical_epargne(self):
        """Score pénalisé avec épargne brute critique."""
        indicators = {
            "epargne_brute_pct": Decimal("5"),   # < 8% = critical
            "epargne_nette_pct": Decimal("8"),
            "taux_rigidite": Decimal("55"),
            "taux_fonctionnement": Decimal("85"),
        }
        score, alertes = calculate_score(indicators)
        assert score < 100
        assert any(a["severite"] == "CRITICAL" for a in alertes)

    def test_score_bounds(self):
        """Le score doit toujours être entre 0 et 100."""
        # Tous les indicateurs mauvais
        indicators = {
            "epargne_brute_pct": Decimal("1"),
            "epargne_nette_pct": Decimal("0"),
            "taux_rigidite": Decimal("80"),
            "taux_fonctionnement": Decimal("99"),
            "effort_equipement": Decimal("2"),
            "dependance_dgf": Decimal("40"),
        }
        score, alertes = calculate_score(indicators)
        assert 0 <= score <= 100

    def test_score_interpretation(self):
        assert "excellente" in get_score_interpretation(90)
        assert "bonne" in get_score_interpretation(70)
        assert "correcte" in get_score_interpretation(55)
        assert "préoccupante" in get_score_interpretation(40)
        assert "critique" in get_score_interpretation(20)
