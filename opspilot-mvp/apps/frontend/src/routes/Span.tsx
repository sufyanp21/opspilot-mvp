import { useState } from 'react'
import { apiClient } from '@/lib/api'
import { SpanDeltaInfo } from '@/lib/types'
import { formatNumber, downloadCSV } from '@/lib/utils'
import FileCard from '@/components/FileCard'
import DataGrid from '@/components/DataGrid'

export default function Span() {
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [deltas, setDeltas] = useState<SpanDeltaInfo[]>([])
  const [loading, setLoading] = useState(false)

  const handleSpanFileUploaded = (file: any) => {
    // Extract date from response if available
    console.log('SPAN file uploaded:', file)
  }

  const loadSpanChanges = async () => {
    if (!selectedDate) return

    setLoading(true)
    try {
      const data = await apiClient.getSpanChanges(selectedDate)
      setDeltas(data)
    } catch (error) {
      console.error('Failed to load SPAN changes:', error)
      alert('Failed to load SPAN changes')
    } finally {
      setLoading(false)
    }
  }

  const downloadDeltasCSV = () => {
    if (!deltas.length) return

    const csvData = deltas.map(delta => ({
      product: delta.product,
      account: delta.account,
      scan_before: delta.scan_before || 0,
      scan_after: delta.scan_after,
      delta: delta.delta
    }))

    downloadCSV(csvData, `span_deltas_${selectedDate}.csv`)
  }

  const sortedDeltas = [...deltas].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">SPAN Margin Analysis</h1>
        <p className="mt-2 text-gray-600">
          Upload SPAN files and analyze margin changes
        </p>
      </div>

      {/* SPAN File Upload */}
      <div className="max-w-md">
        <FileCard
          title="SPAN File"
          description="Upload your SPAN margin file (CSV format)"
          fileKind="span"
          onFileUploaded={handleSpanFileUploaded}
        />
      </div>

      {/* Date Selection */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">View Margin Changes</h2>
        <div className="flex items-center space-x-4">
          <div>
            <label htmlFor="asof-date" className="block text-sm font-medium text-gray-700 mb-1">
              As of Date
            </label>
            <input
              id="asof-date"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={loadSpanChanges}
              disabled={!selectedDate || loading}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                selectedDate && !loading
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {loading ? 'Loading...' : 'Load Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Delta Results */}
      {deltas.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Margin Deltas</h2>
              <p className="text-sm text-gray-600">
                {deltas.length} position{deltas.length !== 1 ? 's' : ''} for {selectedDate}
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={downloadDeltasCSV}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Export CSV
              </button>
            </div>
          </div>

          <DataGrid
            data={sortedDeltas}
            columns={[
              {
                key: 'product',
                label: 'Product'
              },
              {
                key: 'account',
                label: 'Account'
              },
              {
                key: 'scan_before',
                label: 'Previous Margin',
                render: (value: number) => value ? formatNumber(value) : 'N/A'
              },
              {
                key: 'scan_after',
                label: 'Current Margin',
                render: (value: number) => formatNumber(value)
              },
              {
                key: 'delta',
                label: 'Change',
                render: (value: number) => (
                  <span className={`font-medium ${
                    value > 0 ? 'text-red-600' : value < 0 ? 'text-green-600' : 'text-gray-600'
                  }`}>
                    {value > 0 ? '+' : ''}{formatNumber(value)}
                  </span>
                )
              }
            ]}
          />
        </div>
      )}

      {/* Quick Filters */}
      {deltas.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-red-50 p-4 rounded-lg">
              <h4 className="font-medium text-red-800">Largest Increases</h4>
              <p className="text-sm text-red-600 mt-1">
                {sortedDeltas.filter(d => d.delta > 0).length} positions with increased margin
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-800">Largest Decreases</h4>
              <p className="text-sm text-green-600 mt-1">
                {sortedDeltas.filter(d => d.delta < 0).length} positions with decreased margin
              </p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-800">No Change</h4>
              <p className="text-sm text-blue-600 mt-1">
                {sortedDeltas.filter(d => d.delta === 0).length} positions unchanged
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
