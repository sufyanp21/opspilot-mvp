import { useState } from 'react'
import { ColumnMapping } from '@/lib/types'

interface ColumnMapperProps {
  internalColumns: string[]
  clearedColumns: string[]
  onMappingComplete: (mapping: ColumnMapping) => void
}

const standardFields = [
  { key: 'trade_id', label: 'Trade ID', required: true },
  { key: 'account', label: 'Account', required: true },
  { key: 'symbol', label: 'Symbol', required: true },
  { key: 'side', label: 'Side (BUY/SELL)', required: true },
  { key: 'qty', label: 'Quantity', required: true },
  { key: 'price', label: 'Price', required: true },
  { key: 'trade_date', label: 'Trade Date', required: true },
  { key: 'exchange', label: 'Exchange', required: false },
  { key: 'clearing_ref', label: 'Clearing Reference', required: false },
]

export default function ColumnMapper({
  internalColumns,
  clearedColumns,
  onMappingComplete
}: ColumnMapperProps) {
  const [internalMapping, setInternalMapping] = useState<Record<string, string>>({})
  const [clearedMapping, setClearedMapping] = useState<Record<string, string>>({})

  const handleInternalMapping = (standardField: string, csvColumn: string) => {
    setInternalMapping(prev => ({
      ...prev,
      [csvColumn]: standardField
    }))
  }

  const handleClearedMapping = (standardField: string, csvColumn: string) => {
    setClearedMapping(prev => ({
      ...prev,
      [csvColumn]: standardField
    }))
  }

  const handleComplete = () => {
    const mapping: ColumnMapping = {
      internal: internalMapping,
      cleared: clearedMapping
    }
    onMappingComplete(mapping)
  }

  const requiredFieldsMapped = () => {
    const requiredFields = standardFields.filter(f => f.required).map(f => f.key)
    const internalMapped = Object.values(internalMapping)
    const clearedMapped = Object.values(clearedMapping)
    
    return requiredFields.every(field => 
      internalMapped.includes(field) && clearedMapped.includes(field)
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Internal File Mapping */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Internal File Columns</h3>
          <div className="space-y-3">
            {standardFields.map((field) => (
              <div key={`internal-${field.key}`} className="flex items-center space-x-3">
                <div className="w-32 text-sm font-medium text-gray-700">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </div>
                <select
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                  value={Object.keys(internalMapping).find(k => internalMapping[k] === field.key) || ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      handleInternalMapping(field.key, e.target.value)
                    }
                  }}
                >
                  <option value="">Select column...</option>
                  {internalColumns.map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>

        {/* Cleared File Mapping */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Cleared File Columns</h3>
          <div className="space-y-3">
            {standardFields.map((field) => (
              <div key={`cleared-${field.key}`} className="flex items-center space-x-3">
                <div className="w-32 text-sm font-medium text-gray-700">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </div>
                <select
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                  value={Object.keys(clearedMapping).find(k => clearedMapping[k] === field.key) || ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      handleClearedMapping(field.key, e.target.value)
                    }
                  }}
                >
                  <option value="">Select column...</option>
                  {clearedColumns.map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          onClick={handleComplete}
          disabled={!requiredFieldsMapped()}
          className={`px-6 py-2 rounded-md font-medium transition-colors ${
            requiredFieldsMapped()
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Complete Mapping
        </button>
      </div>

      {/* Validation Message */}
      {!requiredFieldsMapped() && (
        <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded-md">
          Please map all required fields (marked with *) for both files before continuing.
        </div>
      )}
    </div>
  )
}
