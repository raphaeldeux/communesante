export interface Commune {
  id: number
  code_insee: string
  siret: string | null
  nom: string
  population: number | null
  departement: string | null
}

export interface ExerciceFinancier {
  id: number
  commune_id: number
  annee: number
  source: 'API' | 'PDF' | 'MANUEL'
  statut: 'BROUILLON' | 'VALIDE' | 'SYNCHRONISE'
  fichier_pdf: string | null
}

export interface LigneFinanciere {
  id: number
  chapitre: string
  article: string | null
  libelle: string
  montant_vote: number | null
  montant_reel: number | null
}

export interface FinancesDetail {
  exercice: ExerciceFinancier
  recettes_fonctionnement: LigneFinanciere[]
  depenses_fonctionnement: LigneFinanciere[]
  recettes_investissement: LigneFinanciere[]
  depenses_investissement: LigneFinanciere[]
  total_recettes_fonctionnement: number
  total_depenses_fonctionnement: number
  total_recettes_investissement: number
  total_depenses_investissement: number
  epargne_brute: number
}

export interface KpiCard {
  code: string
  libelle: string
  valeur: number | null
  unite: string
  seuil_alerte: number | null
  statut: 'ok' | 'warning' | 'critical'
  tendance: 'hausse' | 'baisse' | 'stable' | null
}

export interface ScoreData {
  commune_id: number
  annee: number
  score: number
  interpretation: string
  kpis: KpiCard[]
  alertes_actives: number
}

export interface Alerte {
  id: number
  commune_id: number
  annee: number
  indicateur: string
  severite: 'INFO' | 'WARNING' | 'CRITICAL'
  message: string
  resolue: boolean
  created_at: string
}

export interface EvolutionPoint {
  annee: number
  total_recettes_fonctionnement?: number
  total_depenses_fonctionnement?: number
  epargne_brute?: number
  epargne_brute_pct?: number
  taux_fonctionnement?: number
  taux_rigidite?: number
  score_global?: number
  charges_personnel?: number
  depenses_equipement?: number
}
