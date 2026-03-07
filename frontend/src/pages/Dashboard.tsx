import { useState } from 'react'
import { useScore, useAlertes, useEvolution, useFinancesAll } from '../hooks/useCommune'
import { KpiCard } from '../components/ui/KpiCard'
import { ScoreGauge } from '../components/ui/ScoreGauge'
import { AlerteBanner } from '../components/ui/AlerteBanner'
import { EvolutionChart } from '../components/charts/EvolutionChart'
import { Header } from '../components/layout/Header'

const DEFAULT_INSEE = import.meta.env.VITE_COMMUNE_INSEE || '44196'

export function Dashboard() {
  const [annee, setAnnee] = useState<number | undefined>(undefined)

  const { data: score, isLoading: scoreLoading, error: scoreError } = useScore(DEFAULT_INSEE, annee)
  const { data: alertes } = useAlertes(DEFAULT_INSEE)
  const { data: evolution } = useEvolution(DEFAULT_INSEE)
  const { data: exercices } = useFinancesAll(DEFAULT_INSEE)

  const annees = exercices?.map(e => e.annee).sort((a, b) => b - a) || []

  if (scoreLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (scoreError) {
    return (
      <div className="bg-warning-100 border border-warning-500 rounded-xl p-6 text-center">
        <p className="text-warning-700 font-medium">Aucune donnée disponible</p>
        <p className="text-warning-600 text-sm mt-2">
          Cliquez sur "Synchroniser" dans le menu pour charger les données financières.
        </p>
      </div>
    )
  }

  if (!score) {
    return (
      <div className="bg-warning-100 border border-warning-500 rounded-xl p-6 text-center">
        <p className="text-warning-700 font-medium">Aucune donnée disponible</p>
        <p className="text-warning-600 text-sm mt-2">
          Cliquez sur "Synchroniser" dans le menu pour charger les données financières.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <Header
        title="Tableau de bord"
        subtitle="Vue d'ensemble de la santé financière"
        annee={annee || score.annee}
        annees={annees}
        onAnneeChange={setAnnee}
      />

      {/* Score + Alertes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card flex flex-col items-center justify-center">
          <h3 className="text-sm font-medium text-gray-500 mb-4">Score de santé financière</h3>
          <ScoreGauge score={score.score} interpretation={score.interpretation} />
          <p className="mt-3 text-sm text-gray-500">Exercice {score.annee}</p>
          {score.alertes_actives > 0 && (
            <p className="mt-2 text-xs text-danger-600 font-medium">
              {score.alertes_actives} alerte{score.alertes_actives > 1 ? 's' : ''} active{score.alertes_actives > 1 ? 's' : ''}
            </p>
          )}
        </div>

        <div className="lg:col-span-2 card">
          <h3 className="text-sm font-medium text-gray-500 mb-4">Alertes actives</h3>
          {alertes && alertes.length > 0 ? (
            <AlerteBanner alertes={alertes.filter(a => a.annee === score.annee)} />
          ) : (
            <div className="flex items-center justify-center h-24 text-gray-400">
              <p className="text-sm">Aucune alerte pour cet exercice</p>
            </div>
          )}
        </div>
      </div>

      {/* KPIs */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Indicateurs clés</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {score.kpis.map((kpi) => (
            <KpiCard key={kpi.code} kpi={kpi} />
          ))}
        </div>
      </div>

      {/* Évolution pluriannuelle */}
      {evolution && evolution.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Évolution pluriannuelle
          </h3>
          <EvolutionChart data={evolution} />
        </div>
      )}
    </div>
  )
}
