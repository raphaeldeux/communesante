import { useState } from 'react'
import { useFinancesAnnee, useFinancesAll, useEvolution } from '../hooks/useCommune'
import { BarChart } from '../components/charts/BarChart'
import { Header } from '../components/layout/Header'
import { formatEuros } from '../lib/api'
import { useSelectedCommune } from '../contexts/CommuneContext'

export function Investissements() {
  const { insee } = useSelectedCommune()
  const { data: exercices } = useFinancesAll(insee)
  const annees = exercices?.map(e => e.annee).sort((a, b) => b - a) || []
  const [annee, setAnnee] = useState<number>(annees[0] || new Date().getFullYear())
  const { data: finances, isLoading } = useFinancesAnnee(insee, annee || annees[0])
  const { data: evolution } = useEvolution(insee)

  if (annees.length > 0 && !annee) setAnnee(annees[0])

  const getDepensesEquipement = (f: typeof finances) => {
    if (!f) return 0
    return f.depenses_investissement
      .filter(l => ['20', '21', '23'].includes(l.chapitre))
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  const getRemboursementCapital = (f: typeof finances) => {
    if (!f) return 0
    return f.depenses_investissement
      .filter(l => l.chapitre === '16')
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  const buildInvestEvolution = () => {
    if (!evolution) return []
    return evolution.map(e => ({
      annee: e.annee,
      equipement: e.depenses_equipement,
    }))
  }

  const getAutofinancement = (f: typeof finances) => {
    if (!f) return 0
    return f.recettes_investissement
      .filter(l => l.chapitre === '10')
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  const getEmprunts = (f: typeof finances) => {
    if (!f) return 0
    return f.recettes_investissement
      .filter(l => l.chapitre === '16')
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  return (
    <div className="space-y-8">
      <Header
        title="Investissements"
        subtitle="Volume et financement des investissements"
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
          {/* KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">Dépenses d'équipement</p>
              <p className="text-2xl font-bold text-primary-600 mt-2">
                {formatEuros(getDepensesEquipement(finances))}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Remboursement capital</p>
              <p className="text-2xl font-bold text-danger-700 mt-2">
                {formatEuros(getRemboursementCapital(finances))}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Autofinancement</p>
              <p className="text-2xl font-bold text-success-700 mt-2">
                {formatEuros(getAutofinancement(finances))}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Emprunts nouveaux</p>
              <p className="text-2xl font-bold text-warning-700 mt-2">
                {formatEuros(getEmprunts(finances))}
              </p>
            </div>
          </div>

          {/* Évolution investissement */}
          <div className="card">
            <h3 className="text-base font-semibold text-gray-900 mb-4">
              Évolution des dépenses d'équipement
            </h3>
            <BarChart
              data={buildInvestEvolution()}
              bars={[{ dataKey: 'equipement', name: 'Dépenses équipement', color: '#3b82f6' }]}
            />
          </div>

          {/* Financement de l'investissement */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4">
                Sources de financement
              </h3>
              <div className="space-y-3">
                {[
                  {
                    label: 'Autofinancement propre',
                    value: getAutofinancement(finances),
                    color: 'bg-success-500',
                  },
                  {
                    label: 'Emprunts',
                    value: getEmprunts(finances),
                    color: 'bg-warning-500',
                  },
                  {
                    label: 'Subventions',
                    value: finances.recettes_investissement
                      .filter(l => l.chapitre === '13')
                      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0),
                    color: 'bg-primary-500',
                  },
                  {
                    label: 'FCTVA',
                    value: finances.recettes_investissement
                      .filter(l => l.chapitre === '10' && l.article?.startsWith('10222'))
                      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0),
                    color: 'bg-purple-500',
                  },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${item.color}`} />
                      <span className="text-sm text-gray-600">{item.label}</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatEuros(item.value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4">
                Dépenses d'investissement
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 text-gray-500 font-medium">Libellé</th>
                      <th className="text-right py-2 text-gray-500 font-medium">Montant</th>
                    </tr>
                  </thead>
                  <tbody>
                    {finances.depenses_investissement.map(ligne => (
                      <tr key={ligne.id} className="border-b border-gray-50">
                        <td className="py-2 text-gray-700">{ligne.libelle}</td>
                        <td className="py-2 text-right font-medium text-gray-900">
                          {formatEuros(Number(ligne.montant_reel || ligne.montant_vote))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
