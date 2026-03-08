import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import type { Commune, FinancesDetail, ScoreData, Alerte, EvolutionPoint, ExerciceFinancier } from '../types'

export function useListCommunes() {
  return useQuery<Commune[]>({
    queryKey: ['communes'],
    queryFn: () => api.get('/communes/').then(r => Array.isArray(r.data) ? r.data : []),
  })
}

export function useCommune(insee: string) {
  return useQuery<Commune>({
    queryKey: ['commune', insee],
    queryFn: () => api.get(`/communes/${insee}`).then(r => r.data),
  })
}

export function useFinancesAll(insee: string) {
  return useQuery<ExerciceFinancier[]>({
    queryKey: ['finances-all', insee],
    queryFn: () => api.get(`/communes/${insee}/finances`).then(r => r.data),
  })
}

export function useFinancesAnnee(insee: string, annee: number) {
  return useQuery<FinancesDetail>({
    queryKey: ['finances', insee, annee],
    queryFn: () => api.get(`/communes/${insee}/finances/${annee}`).then(r => r.data),
    enabled: !!annee,
  })
}

export function useScore(insee: string, annee?: number) {
  const params = annee ? { annee } : {}
  return useQuery<ScoreData>({
    queryKey: ['score', insee, annee],
    queryFn: () => api.get(`/communes/${insee}/score`, { params }).then(r => r.data),
  })
}

export function useAlertes(insee: string) {
  return useQuery<Alerte[]>({
    queryKey: ['alertes', insee],
    queryFn: () => api.get(`/communes/${insee}/alertes`).then(r => r.data),
  })
}

export function useEvolution(insee: string) {
  return useQuery<EvolutionPoint[]>({
    queryKey: ['evolution', insee],
    queryFn: () => api.get(`/communes/${insee}/evolution`).then(r => r.data),
  })
}

export function useSync(insee: string) {
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
