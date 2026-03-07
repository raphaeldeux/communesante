import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { formatValue } from '../../lib/api'
import type { KpiCard as KpiCardType } from '../../types'

interface Props {
  kpi: KpiCardType
}

const statusConfig = {
  ok: {
    bg: 'bg-success-100',
    text: 'text-success-700',
    border: 'border-success-500',
    icon: CheckCircle,
    iconColor: 'text-success-500',
    label: 'Bon',
  },
  warning: {
    bg: 'bg-warning-100',
    text: 'text-warning-700',
    border: 'border-warning-500',
    icon: AlertTriangle,
    iconColor: 'text-warning-500',
    label: 'Vigilance',
  },
  critical: {
    bg: 'bg-danger-100',
    text: 'text-danger-700',
    border: 'border-danger-500',
    icon: XCircle,
    iconColor: 'text-danger-500',
    label: 'Critique',
  },
}

export function KpiCard({ kpi }: Props) {
  const config = statusConfig[kpi.statut] || statusConfig.ok
  const Icon = config.icon

  const TrendIcon =
    kpi.tendance === 'hausse' ? TrendingUp :
    kpi.tendance === 'baisse' ? TrendingDown :
    Minus

  return (
    <div className={`card border-l-4 ${config.border}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-500 font-medium">{kpi.libelle}</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">
            {formatValue(kpi.valeur, kpi.unite)}
          </p>
          {kpi.seuil_alerte !== null && (
            <p className="mt-1 text-xs text-gray-400">
              Seuil: {formatValue(kpi.seuil_alerte, kpi.unite)}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          <Icon className={`w-5 h-5 ${config.iconColor}`} />
          {kpi.tendance && (
            <TrendIcon className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>
      <div className={`mt-3 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </div>
    </div>
  )
}
