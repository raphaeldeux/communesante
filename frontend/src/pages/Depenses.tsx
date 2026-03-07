import { useState } from 'react'
import { useFinancesAnnee, useFinancesAll, useEvolution } from '../hooks/useCommune'
import { RepartitionPieChart } from '../components/charts/RepartitionPieChart'
import { BarChart } from '../components/charts/BarChart'
import { Header } from '../components/layout/Header'
import { formatEuros } from '../lib/api'

const DEFAULT_INSEE = import.meta.env.VITE_COMMUNE_INSEE || '44196'

export function Depenses() {
  const { data: exercices } = useFinancesAll(DEFAULT_INSEE)
  const annees = exercices?.map(e => e.annee).sort((a, b) => b - a) || []
  const [annee, setAnnee] = useState<number>(annees[0] || new Date().getFullYear())
  const { data: finances, isLoading } = useFinancesAnnee(DEFAULT_INSEE, annee || annees[0])
  const { data: evolution } = useEvolution(DEFAULT_INSEE)

  if (annees.length > 0 && !annee) setAnnee(annees[0])

  const buildPieData = () => {
    if (!finances) return []
    const chapitres: Record<string, { name: string; value: number }> = {}
    for (const ligne of finances.depenses_fonctionnement) {
      const montant = Number(ligne.montant_reel || ligne.montant_vote || 0)
      const key = ligne.libelle.length > 30 ? ligne.libelle.slice(0, 30) + '…' : ligne.libelle
      if (!chapitres[key]) chapitres[key] = { name: key, value: 0 }
      chapitres[key].value += montant
    }
    return Object.values(chapitres).filter(d => d.value > 0).sort((a, b) => b.value - a.value).slice(0, 8)
  }

  const buildPersonnelEvolution = () => {
    if (!evolution) return []
    return evolution.map(e => ({
      annee: e.annee,
      personnel: e.charges_personnel,
    }))
  }

  const getPersonnelRatio = () => {
    if (!finances) return null
    const personnel = finances.depenses_fonctionnement
      .filter(l => l.chapitre === '012')
      .reduce((sum, l) => sum + Number(l.montant_reel || l.montant_vote || 0), 0)
    const total = Number(finances.total_depenses_fonctionnement)
    if (total === 0) return null
    return ((personnel / total) * 100).toFixed(1)
  }

  return (
    <div className="space-y-8">
      <Header
        title="Dépenses"
        subtitle="Structure et évolution des dépenses de fonctionnement"
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
          {/* KPIs rapides */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">Total dépenses fonctionnement</p>
              <p className="text-2xl font-bold text-danger-700 mt-2">
                {formatEuros(Number(finances.total_depenses_fonctionnement))}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Charges de personnel</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {formatEuros(
                  finances.depenses_fonctionnement
                    .filter(l => l.chapitre === '012')
                    .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
                )}
              </p>
              {getPersonnelRatio() && (
                <p className="text-sm text-gray-500 mt-1">{getPersonnelRatio()}% des dépenses</p>
              )}
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Charges générales (ch. 011)</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {formatEuros(
                  finances.depenses_fonctionnement
                    .filter(l => l.chapitre === '011')
                    .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
                )}
              </p>
            </div>
          </div>

          {/* Répartition + Personnel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <RepartitionPieChart
                data={buildPieData()}
                title="Répartition des dépenses de fonctionnement"
              />
            </div>
            <div className="card">
              <h3 className="text-base font-semibold text-gray-700 mb-4">
                Évolution des charges de personnel
              </h3>
              <BarChart
                data={buildPersonnelEvolution()}
                bars={[{ dataKey: 'personnel', name: 'Charges personnel', color: '#8b5cf6' }]}
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
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">% Total</th>
                  </tr>
                </thead>
                <tbody>
                  {finances.depenses_fonctionnement.map((ligne) => {
                    const montant = Number(ligne.montant_reel || ligne.montant_vote || 0)
                    const pct = Number(finances.total_depenses_fonctionnement) > 0
                      ? ((montant / Number(finances.total_depenses_fonctionnement)) * 100).toFixed(1)
                      : '–'
                    return (
                      <tr key={ligne.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 px-3 font-mono text-xs text-gray-500">{ligne.chapitre}</td>
                        <td className="py-2 px-3 text-gray-700">{ligne.libelle}</td>
                        <td className="py-2 px-3 text-right text-gray-600">
                          {formatEuros(Number(ligne.montant_vote))}
                        </td>
                        <td className="py-2 px-3 text-right font-medium text-gray-900">
                          {formatEuros(montant)}
                        </td>
                        <td className="py-2 px-3 text-right text-gray-500 text-xs">{pct}%</td>
                      </tr>
                    )
                  })}
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
