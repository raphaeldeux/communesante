import { useState, useRef, useEffect } from 'react'
import { Search, ChevronDown, Plus, Check } from 'lucide-react'
import { useListCommunes, useCommune } from '../../hooks/useCommune'
import { useSelectedCommune } from '../../contexts/CommuneContext'
import { useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'

export function CommuneSelector() {
  const { insee, setInsee } = useSelectedCommune()
  const { data: communes = [] } = useListCommunes()
  const { data: current } = useCommune(insee)
  const queryClient = useQueryClient()

  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [newInsee, setNewInsee] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  // Fermer le dropdown en cliquant ailleurs
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const filtered = communes.filter(c =>
    c.nom.toLowerCase().includes(search.toLowerCase()) ||
    c.code_insee.includes(search)
  )

  const handleSelect = (code: string) => {
    setInsee(code)
    setOpen(false)
    setSearch('')
  }

  const handleAdd = async () => {
    const code = newInsee.trim()
    if (!/^\d{5}$/.test(code)) {
      setAddError('Code INSEE invalide (5 chiffres)')
      return
    }
    setAdding(true)
    setAddError('')
    try {
      await api.get(`/communes/${code}`)
      queryClient.invalidateQueries({ queryKey: ['communes'] })
      setInsee(code)
      setNewInsee('')
      setOpen(false)
    } catch {
      setAddError('Commune introuvable')
    } finally {
      setAdding(false)
    }
  }

  return (
    <div ref={ref} className="relative px-4 py-3 bg-primary-800">
      <p className="text-xs text-primary-300 uppercase tracking-wider mb-1">Commune</p>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-2 text-left"
      >
        <span className="text-sm font-semibold text-white truncate">
          {current?.nom ?? insee}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-primary-300 flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full mt-1 z-50 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
          {/* Recherche */}
          <div className="p-2 border-b border-gray-100">
            <div className="flex items-center gap-2 px-2 py-1.5 bg-gray-50 rounded-md">
              <Search className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
              <input
                autoFocus
                type="text"
                placeholder="Rechercher…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-gray-700 outline-none placeholder-gray-400"
              />
            </div>
          </div>

          {/* Liste des communes */}
          <ul className="max-h-48 overflow-y-auto">
            {filtered.length === 0 ? (
              <li className="px-3 py-2 text-xs text-gray-400 text-center">Aucune commune trouvée</li>
            ) : (
              filtered.map(c => (
                <li key={c.code_insee}>
                  <button
                    onClick={() => handleSelect(c.code_insee)}
                    className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-primary-50 transition-colors"
                  >
                    <div>
                      <span className="text-sm font-medium text-gray-800">{c.nom}</span>
                      <span className="ml-2 text-xs text-gray-400">{c.code_insee}</span>
                    </div>
                    {c.code_insee === insee && (
                      <Check className="w-4 h-4 text-primary-600 flex-shrink-0" />
                    )}
                  </button>
                </li>
              ))
            )}
          </ul>

          {/* Ajouter une commune par code INSEE */}
          <div className="p-2 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-500 mb-1.5">Ajouter une commune</p>
            <div className="flex gap-1.5">
              <input
                type="text"
                placeholder="Code INSEE (5 chiffres)"
                value={newInsee}
                onChange={e => { setNewInsee(e.target.value); setAddError('') }}
                onKeyDown={e => e.key === 'Enter' && handleAdd()}
                maxLength={5}
                className="flex-1 px-2 py-1.5 text-sm border border-gray-200 rounded-md outline-none focus:border-primary-400"
              />
              <button
                onClick={handleAdd}
                disabled={adding}
                className="flex items-center gap-1 px-2 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs rounded-md disabled:opacity-50 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                {adding ? '…' : 'Ajouter'}
              </button>
            </div>
            {addError && <p className="text-xs text-red-500 mt-1">{addError}</p>}
          </div>
        </div>
      )}
    </div>
  )
}
