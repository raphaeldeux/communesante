import { AlertTriangle, XCircle, Info } from 'lucide-react'
import type { Alerte } from '../../types'

interface Props {
  alertes: Alerte[]
}

const severiteConfig = {
  INFO: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    icon: Info,
    iconColor: 'text-blue-500',
  },
  WARNING: {
    bg: 'bg-warning-100',
    border: 'border-warning-500',
    text: 'text-warning-700',
    icon: AlertTriangle,
    iconColor: 'text-warning-500',
  },
  CRITICAL: {
    bg: 'bg-danger-100',
    border: 'border-danger-500',
    text: 'text-danger-700',
    icon: XCircle,
    iconColor: 'text-danger-500',
  },
}

export function AlerteBanner({ alertes }: Props) {
  if (!alertes || alertes.length === 0) return null

  const critical = alertes.filter(a => a.severite === 'CRITICAL')
  const warning = alertes.filter(a => a.severite === 'WARNING')
  const toShow = [...critical, ...warning].slice(0, 3)

  return (
    <div className="space-y-2">
      {toShow.map((alerte) => {
        const config = severiteConfig[alerte.severite]
        const Icon = config.icon
        return (
          <div
            key={alerte.id}
            className={`flex items-start gap-3 p-3 rounded-lg border ${config.bg} ${config.border}`}
          >
            <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
            <div>
              <p className={`text-sm font-medium ${config.text}`}>{alerte.message}</p>
              <p className={`text-xs mt-0.5 opacity-70 ${config.text}`}>Exercice {alerte.annee}</p>
            </div>
          </div>
        )
      })}
      {alertes.length > 3 && (
        <p className="text-sm text-gray-500 text-center">
          +{alertes.length - 3} autre(s) alerte(s)
        </p>
      )}
    </div>
  )
}
