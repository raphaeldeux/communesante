import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { formatEuros } from '../../lib/api'

interface DataItem {
  name: string
  value: number
  chapitre?: string
}

interface Props {
  data: DataItem[]
  title?: string
}

const COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#14b8a6',
]

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null
  const item = payload[0]
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-900">{item.name}</p>
      <p className="text-sm text-gray-600">{formatEuros(item.value)}</p>
      <p className="text-sm text-gray-500">{(item.payload.percent * 100).toFixed(1)}%</p>
    </div>
  )
}

export function RepartitionPieChart({ data, title }: Props) {
  const total = data.reduce((sum, d) => sum + d.value, 0)

  return (
    <div>
      {title && <h3 className="text-base font-semibold text-gray-700 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value) => (
              <span className="text-xs text-gray-600">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      <p className="text-center text-sm text-gray-500 mt-2">
        Total: <span className="font-semibold">{formatEuros(total)}</span>
      </p>
    </div>
  )
}
