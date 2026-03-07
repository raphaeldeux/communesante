import { useState } from 'react'
import { useFinancesAnnee, useFinancesAll, useEvolution } from '../hooks/useCommune'
import { EvolutionChart } from '../components/charts/EvolutionChart'
import { Header } from '../components/layout/Header'
import { formatEuros, formatAns } from '../lib/api'
import { useSelectedCommune } from '../contexts/CommuneContext'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'

export function Dette() {
  const { insee } = useSelectedCommune()
  const { data: exercices } = useFinancesAll(insee)
  const annees = exercices?.map(e => e.annee).sort((a, b) => b - a) || []
  const [annee, setAnnee] = useState<number>(annees[0] || new Date().getFullYear())
  const { data: finances, isLoading } = useFinancesAnnee(insee, annee || annees[0])
  const { data: evolution } = useEvolution(insee)

  if (annees.length > 0 && !annee) setAnnee(annees[0])

  const getInteretsDette = (f: typeof finances) => {
    if (!f) return 0
    return f.depenses_fonctionnement
      .filter(l => l.chapitre === '66')
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  const getRemboursementCapital = (f: typeof finances) => {
    if (!f) return 0
    return f.depenses_investissement
      .filter(l => l.chapitre === '16')
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  const getNouveauxEmprunts = (f: typeof finances) => {
    if (!f) return 0
    return f.recettes_investissement
      .filter(l => l.chapitre === '16')
      .reduce((s, l) => s + Number(l.montant_reel || l.montant_vote || 0), 0)
  }

  const buildCapDesendettement = () => {
    if (!evolution) return []
    return evolution.map(e => {
      const epargne = e.epargne_brute || 0
      // Estimer l'encours à partir des flux (simplification)
      const cap = epargne > 0 ? null : null // nécessite l'encours réel
      return {
        annee: e.annee,
        epargne_brute: epargne,
      }
    })
  }

  return (
    <div className="space-y-8">
      <Header
        title="Dette"
        subtitle="Analyse de la dette et capacité de désendettement"
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
          {/* KPIs dette */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">Intérêts de la dette</p>
              <p className="text-2xl font-bold text-danger-700 mt-2">
                {formatEuros(getInteretsDette(finances))}
              </p>
              <p className="text-xs text-gray-400 mt-1">Section fonctionnement – Ch. 66</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Remboursement capital</p>
              <p className="text-2xl font-bold text-warning-700 mt-2">
                {formatEuros(getRemboursementCapital(finances))}
              </p>
              <p className="text-xs text-gray-400 mt-1">Section investissement – Ch. 16</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Nouveaux emprunts</p>
              <p className="text-2xl font-bold text-primary-600 mt-2">
                {formatEuros(getNouveauxEmprunts(finances))}
              </p>
              <p className="text-xs text-gray-400 mt-1">Recettes investissement – Ch. 16</p>
            </div>
          </div>

          {/* Flux nets */}
          <div className="card">
            <h3 className="text-base font-semibold text-gray-900 mb-2">
              Flux nets de dette
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Nouveaux emprunts – Remboursement capital
            </p>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-500">Nouveaux emprunts</p>
                <p className="text-xl font-bold text-primary-600">
                  {formatEuros(getNouveauxEmprunts(finances))}
                </p>
              </div>
              <span className="text-2xl text-gray-400">–</span>
              <div className="text-center">
                <p className="text-sm text-gray-500">Remb. capital</p>
                <p className="text-xl font-bold text-danger-700">
                  {formatEuros(getRemboursementCapital(finances))}
                </p>
              </div>
              <span className="text-2xl text-gray-400">=</span>
              <div className="text-center">
                <p className="text-sm text-gray-500">Variation nette</p>
                <p className={`text-xl font-bold ${
                  getNouveauxEmprunts(finances) - getRemboursementCapital(finances) >= 0
                    ? 'text-warning-700' : 'text-success-700'
                }`}>
                  {formatEuros(getNouveauxEmprunts(finances) - getRemboursementCapital(finances))}
                </p>
              </div>
            </div>
          </div>

          {/* Évolution épargne brute */}
          {evolution && evolution.length > 0 && (
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4">
                Évolution de l'épargne brute (capacité de remboursement)
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={buildCapDesendettement()} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="annee" tick={{ fontSize: 12 }} />
                  <YAxis
                    tickFormatter={(v) => `${(v / 1_000_000).toFixed(1)}M€`}
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip
                    formatter={(v: number) => [formatEuros(v), 'Épargne brute']}
                    labelFormatter={(l) => `Année ${l}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="epargne_brute"
                    name="Épargne brute"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Note sur l'encours */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <p className="text-sm text-blue-800 font-medium">
              Information sur l'encours de la dette
            </p>
            <p className="text-sm text-blue-700 mt-1">
              L'encours total de la dette et la capacité de désendettement précise (en années)
              nécessitent les données de stock issues du compte de gestion définitif DGFiP.
              Ces données seront disponibles après synchronisation avec l'API DGFiP officielle.
            </p>
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
