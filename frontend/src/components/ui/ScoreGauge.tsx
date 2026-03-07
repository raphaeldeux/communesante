interface Props {
  score: number
  interpretation: string
}

export function ScoreGauge({ score, interpretation }: Props) {
  const getColor = (s: number) => {
    if (s >= 80) return { stroke: '#22c55e', text: 'text-success-700', bg: 'bg-success-100' }
    if (s >= 65) return { stroke: '#84cc16', text: 'text-lime-700', bg: 'bg-lime-100' }
    if (s >= 50) return { stroke: '#eab308', text: 'text-warning-700', bg: 'bg-warning-100' }
    if (s >= 35) return { stroke: '#f97316', text: 'text-orange-700', bg: 'bg-orange-100' }
    return { stroke: '#ef4444', text: 'text-danger-700', bg: 'bg-danger-100' }
  }

  const { stroke, text, bg } = getColor(score)

  // SVG arc
  const radius = 60
  const circumference = Math.PI * radius // demi-cercle
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg width="160" height="90" viewBox="0 0 160 90">
          {/* Track */}
          <path
            d="M 10 80 A 70 70 0 0 1 150 80"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Progress */}
          <path
            d="M 10 80 A 70 70 0 0 1 150 80"
            fill="none"
            stroke={stroke}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-4xl font-bold text-gray-900">{score}</span>
          <span className="text-sm text-gray-500">/100</span>
        </div>
      </div>
      <div className={`mt-2 px-3 py-1 rounded-full text-sm font-medium ${bg} ${text}`}>
        {interpretation}
      </div>
    </div>
  )
}
