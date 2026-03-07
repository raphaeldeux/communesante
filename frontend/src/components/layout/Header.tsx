interface Props {
  title: string
  subtitle?: string
  annee?: number
  annees?: number[]
  onAnneeChange?: (annee: number) => void
}

export function Header({ title, subtitle, annee, annees, onAnneeChange }: Props) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        {subtitle && <p className="text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {annees && annees.length > 0 && onAnneeChange && (
        <select
          value={annee}
          onChange={(e) => onAnneeChange(Number(e.target.value))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          {annees.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}
