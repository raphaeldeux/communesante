import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  TrendingDown,
  Building2,
  CreditCard,
  RefreshCw,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Tableau de bord', icon: LayoutDashboard, end: true },
  { to: '/recettes', label: 'Recettes', icon: TrendingUp },
  { to: '/depenses', label: 'Dépenses', icon: TrendingDown },
  { to: '/investissements', label: 'Investissements', icon: Building2 },
  { to: '/dette', label: 'Dette', icon: CreditCard },
]

interface Props {
  communeNom?: string
  onSync?: () => void
  isSyncing?: boolean
}

export function Sidebar({ communeNom, onSync, isSyncing }: Props) {
  return (
    <aside className="w-64 bg-primary-900 text-white flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-primary-700">
        <h1 className="text-xl font-bold text-white">CommuneSante</h1>
        <p className="text-xs text-primary-100 mt-1">Tableau de bord financier</p>
      </div>

      {/* Commune */}
      {communeNom && (
        <div className="px-4 py-3 bg-primary-800">
          <p className="text-xs text-primary-300 uppercase tracking-wider">Commune</p>
          <p className="text-sm font-semibold text-white mt-0.5">{communeNom}</p>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-primary-200 hover:bg-primary-800 hover:text-white'
              )
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Sync button */}
      <div className="p-4 border-t border-primary-700">
        <button
          onClick={onSync}
          disabled={isSyncing}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary-700 hover:bg-primary-600 text-sm text-primary-100 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={clsx('w-4 h-4', isSyncing && 'animate-spin')} />
          {isSyncing ? 'Synchronisation...' : 'Synchroniser'}
        </button>
        <p className="text-xs text-primary-400 mt-2 text-center">
          Données DGFiP / data.gouv.fr
        </p>
      </div>
    </aside>
  )
}
