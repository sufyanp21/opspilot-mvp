import { cn } from '@/lib/utils'

interface KPICardProps {
  title: string
  value: string | number
  icon: string
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'gray'
  subtitle?: string
}

const colorClasses = {
  blue: 'bg-blue-50 text-blue-700 border-blue-200',
  green: 'bg-green-50 text-green-700 border-green-200',
  red: 'bg-red-50 text-red-700 border-red-200',
  yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  gray: 'bg-gray-50 text-gray-700 border-gray-200',
}

export default function KPICard({
  title,
  value,
  icon,
  color = 'gray',
  subtitle
}: KPICardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={cn(
          'flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center border',
          colorClasses[color]
        )}>
          <span className="text-xl">{icon}</span>
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  )
}
