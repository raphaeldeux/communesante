import {
  BarChart as RechartsBar,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { formatEuros } from '../../lib/api'

interface DataPoint {
  annee: number
  [key: string]: number | undefined
}

interface BarConfig {
  dataKey: string
  name: string
  color: string
}

interface Props {
  data: DataPoint[]
  bars: BarConfig[]
  formatY?: (v: number) => string
}

const defaultFormatY = (v: number) => {
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M€`
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}k€`
  return `${v}€`
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-900 mb-2">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {formatEuros(entry.value)}
        </p>
      ))}
    </div>
  )
}

export function BarChart({ data, bars, formatY = defaultFormatY }: Props) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <RechartsBar data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="annee" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={formatY} tick={{ fontSize: 11 }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {bars.map(bar => (
          <Bar key={bar.dataKey} dataKey={bar.dataKey} name={bar.name} fill={bar.color} radius={[4, 4, 0, 0]} />
        ))}
      </RechartsBar>
    </ResponsiveContainer>
  )
}
