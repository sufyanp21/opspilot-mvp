import { ReactNode } from 'react'

interface Column<T = any> {
  key: string
  label: string
  render?: (value: any, row: T) => ReactNode
  sortable?: boolean
}

interface DataGridProps<T = any> {
  data: T[]
  columns: Column<T>[]
  onRowClick?: (row: T) => void
}

export default function DataGrid<T extends Record<string, any>>({
  data,
  columns,
  onRowClick
}: DataGridProps<T>) {
  if (!data.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data available
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, index) => (
            <tr
              key={index}
              className={onRowClick ? 'hover:bg-gray-50 cursor-pointer' : ''}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                >
                  {column.render
                    ? column.render(row[column.key], row)
                    : row[column.key]
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
