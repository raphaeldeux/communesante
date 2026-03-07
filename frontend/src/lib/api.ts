import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Injecter le token API depuis localStorage si disponible
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_token')
  if (token) {
    config.headers['X-API-Token'] = token
  }
  return config
})

export default api

export const formatEuros = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '–'
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)} M€`
  }
  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(0)} k€`
  }
  return `${value.toFixed(0)} €`
}

export const formatPct = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '–'
  return `${value.toFixed(1)} %`
}

export const formatAns = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '–'
  return `${value.toFixed(1)} ans`
}

export const formatValue = (value: number | null | undefined, unite: string): string => {
  if (value === null || value === undefined) return '–'
  if (unite === '€') return formatEuros(value)
  if (unite === '%') return formatPct(value)
  if (unite === 'ans') return formatAns(value)
  return `${value} ${unite}`
}
