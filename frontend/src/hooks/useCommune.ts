import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import type { Commune, FinancesDetail, ScoreData, Alerte, EvolutionPoint, ExerciceFinancier } from '../types'

const DEFAULT_INSEE = import.meta.env.VITE_COMMUNE_INSEE || '44196'

export function useCommune(insee = DEFAULT_INSEE) {
  return useQuery<Commune>({
    queryKey: ['commune', insee],
    queryFn: () => api.get(`/communes/${insee}`).then(r => r.data),
  })
}

export function useFinancesAll(insee = DEFAULT_INSEE) {
  return useQuery<ExerciceFinancier[]>({
    queryKey: ['finances-all', insee],
    queryFn: () => api.get(`/communes/${insee}/finances`).then(r => r.data),
  })
}

export function useFinancesAnnee(insee = DEFAULT_INSEE, annee: number) {
  return useQuery<FinancesDetail>({
    queryKey: ['finances', insee, annee],
    queryFn: () => api.get(`/communes/${insee}/finances/${annee}`).then(r => r.data),
    enabled: !!annee,
  })
}

export function useScore(insee = DEFAULT_INSEE, annee?: number) {
  const params = annee ? { annee } : {}
  return useQuery<ScoreData>({
    queryKey: ['score', insee, annee],
    queryFn: () => api.get(`/communes/${insee}/score`, { params }).then(r => r.data),
  })
}

export function useAlertes(insee = DEFAULT_INSEE) {
  return useQuery<Alerte[]>({
    queryKey: ['alertes', insee],
    queryFn: () => api.get(`/communes/${insee}/alertes`).then(r => r.data),
  })
}

export function useEvolution(insee = DEFAULT_INSEE) {
  return useQuery<EvolutionPoint[]>({
    queryKey: ['evolution', insee],
    queryFn: () => api.get(`/communes/${insee}/evolution`).then(r => r.data),
  })
}

export function useSync(insee = DEFAULT_INSEE) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.post(`/communes/${insee}/sync`).then(r => r.data),
    onSuccess: () => {
      // Invalider toutes les requêtes liées à cette commune après sync
      queryClient.invalidateQueries({ queryKey: ['commune', insee] })
      queryClient.invalidateQueries({ queryKey: ['finances-all', insee] })
      queryClient.invalidateQueries({ queryKey: ['score', insee] })
      queryClient.invalidateQueries({ queryKey: ['evolution', insee] })
    },
  })
}
