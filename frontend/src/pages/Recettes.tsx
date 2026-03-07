import { useState } from 'react'
import { useFinancesAnnee, useFinancesAll, useEvolution } from '../hooks/useCommune'
import { RepartitionPieChart } from '../components/charts/RepartitionPieChart'
import { BarChart } from '../components/charts/BarChart'
import { Header } from '../components/layout/Header'
import { formatEuros } from '../lib/api'

const DEFAULT_INSEE = import.meta.env.VITE_COMMUNE_INSEE || '44196'

export function Recettes() {
  const { data: exercices } = useFinancesAll(DEFAULT_INSEE)
  const annees = exercices?.map(e => e.annee).sort((a, b) => b - a) || []
  const [annee, setAnnee] = useState<number>(annees[0] || new Date().getFullYear())

  const { data: finances, isLoading } = useFinancesAnnee(DEFAULT_INSEE, annee || annees[0])
  const { data: evolution } = useEvolution(DEFAULT_INSEE)

  if (annees.length > 0 && !annee) {
    setAnnee(annees[0])
  }

  const buildPieData = () => {
    if (!finances) return []
    const chapitres: Record<string, { name: string; value: number }> = {}
    for (const ligne of finances.recettes_fonctionnement) {
      const key = `Ch. ${ligne.chapitre}`
      const montant = Number(ligne.montant_reel || ligne.montant_vote || 0)
      if (!chapitres[key]) chapitres[key] = { name: key, value: 0 }
      chapitres[key].value += montant
    }
    return Object.values(chapitres).filter(d => d.value > 0).sort((a, b) => b.value - a.value)
  }

  const buildFiscaliteData = () => {
    if (!evolution) return []
    return evolution.map(e => ({
      annee: e.annee,
      recettes: e.total_recettes_fonctionnement,
      depenses: e.total_depenses_fonctionnement,
    }))
  }

  return (
    <div className="space-y-8">
      <Header
        title="Recettes"
        subtitle="Analyse des recettes de fonctionnement"
        annee={annee}
        annees={annees}
        onAnneeChange={setAnnee}
      />

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : finances ? (
        <>
          {/* Totaux */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">Total recettes fonctionnement</p>
              <p className="text-2xl font-bold text-primary-600 mt-2">
                {formatEuros(Number(finances.total_recettes_fonctionnement))}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Total recettes investissement</p>
              <p className="text-2xl font-bold text-primary-600 mt-2">
                {formatEuros(Number(finances.total_recettes_investissement))}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Épargne brute</p>
              <p className={`text-2xl font-bold mt-2 ${Number(finances.epargne_brute) >= 0 ? 'text-success-700' : 'text-danger-700'}`}>
                {formatEuros(Number(finances.epargne_brute))}
              </p>
            </div>
          </div>

          {/* Répartition + Évolution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <RepartitionPieChart
                data={buildPieData()}
                title="Répartition des recettes de fonctionnement"
              />
            </div>
            <div className="card">
              <h3 className="text-base font-semibold text-gray-700 mb-4">
                Évolution recettes vs dépenses
              </h3>
              <BarChart
                data={buildFiscaliteData()}
                bars={[
                  { dataKey: 'recettes', name: 'Recettes', color: '#3b82f6' },
                  { dataKey: 'depenses', name: 'Dépenses', color: '#ef4444' },
                ]}
              />
            </div>
          </div>

          {/* Tableau détaillé */}
          <div className="card">
            <h3 className="text-base font-semibold text-gray-900 mb-4">
              Détail par chapitre – Fonctionnement
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Chapitre</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Libellé</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Voté</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Réalisé</th>
                  </tr>
                </thead>
                <tbody>
                  {finances.recettes_fonctionnement.map((ligne) => (
                    <tr key={ligne.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 px-3 font-mono text-xs text-gray-500">{ligne.chapitre}</td>
                      <td className="py-2 px-3 text-gray-700">{ligne.libelle}</td>
                      <td className="py-2 px-3 text-right text-gray-600">
                        {formatEuros(Number(ligne.montant_vote))}
                      </td>
                      <td className="py-2 px-3 text-right font-medium text-gray-900">
                        {formatEuros(Number(ligne.montant_reel || ligne.montant_vote))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="card text-center py-12 text-gray-400">
          Aucune donnée disponible pour {annee}
        </div>
      )}
    </div>
  )
}
