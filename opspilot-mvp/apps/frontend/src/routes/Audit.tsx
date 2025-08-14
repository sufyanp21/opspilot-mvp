import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import DataGrid from '@/components/DataGrid'

interface AuditEvent {
  id: string
  timestamp: string
  event_type: string
  user_id?: string
  resource_type: string
  resource_id: string
  details: Record<string, any>
}

export default function Audit() {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState<string>('all')
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days ago
    end: new Date().toISOString().split('T')[0] // today
  })

  useEffect(() => {
    loadAuditEvents()
  }, [])

  const loadAuditEvents = async () => {
    setLoading(true)
    try {
      // Mock audit events for demo
      const mockEvents: AuditEvent[] = [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          event_type: 'file_upload',
          user_id: 'system',
          resource_type: 'file',
          resource_id: 'internal_trades.csv',
          details: { file_size: 1024, file_kind: 'internal' }
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 60000).toISOString(),
          event_type: 'reconciliation_run',
          user_id: 'system',
          resource_type: 'recon_run',
          resource_id: 'run-123',
          details: { total_trades: 150, exceptions: 5 }
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          event_type: 'span_upload',
          user_id: 'system',
          resource_type: 'file',
          resource_id: 'span_margins.csv',
          details: { file_size: 2048, as_of_date: '2024-01-15' }
        }
      ]
      setEvents(mockEvents)
    } catch (error) {
      console.error('Failed to load audit events:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredEvents = events.filter(event => 
    filterType === 'all' || event.event_type === filterType
  )

  const eventTypes = ['all', ...Array.from(new Set(events.map(e => e.event_type)))]

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'file_upload': return '📁'
      case 'reconciliation_run': return '🔄'
      case 'span_upload': return '📊'
      case 'exception_resolved': return '✅'
      default: return '📝'
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'file_upload': return 'bg-blue-100 text-blue-800'
      case 'reconciliation_run': return 'bg-purple-100 text-purple-800'
      case 'span_upload': return 'bg-green-100 text-green-800'
      case 'exception_resolved': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Trail</h1>
        <p className="mt-2 text-gray-600">
          Track all system activities and changes
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Event Type
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              {eventTypes.map(type => (
                <option key={type} value={type}>
                  {type === 'all' ? 'All Types' : type.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">📁</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">File Uploads</p>
              <p className="text-2xl font-bold text-gray-900">
                {events.filter(e => e.event_type === 'file_upload').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">🔄</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Reconciliations</p>
              <p className="text-2xl font-bold text-gray-900">
                {events.filter(e => e.event_type === 'reconciliation_run').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">📊</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">SPAN Uploads</p>
              <p className="text-2xl font-bold text-gray-900">
                {events.filter(e => e.event_type === 'span_upload').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-gray-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">📝</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Events</p>
              <p className="text-2xl font-bold text-gray-900">{events.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Events Table */}
      {filteredEvents.length > 0 ? (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Activity ({filteredEvents.length} events)
            </h2>
          </div>
          <DataGrid
            data={filteredEvents}
            columns={[
              {
                key: 'timestamp',
                label: 'Time',
                render: (value: string) => formatDateTime(value)
              },
              {
                key: 'event_type',
                label: 'Event',
                render: (value: string) => (
                  <div className="flex items-center space-x-2">
                    <span>{getEventIcon(value)}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEventColor(value)}`}>
                      {value.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                )
              },
              {
                key: 'resource_type',
                label: 'Resource',
                render: (value: string) => (
                  <span className="text-sm text-gray-600">{value}</span>
                )
              },
              {
                key: 'resource_id',
                label: 'Resource ID',
                render: (value: string) => (
                  <span className="text-sm font-mono text-gray-900">
                    {value.length > 20 ? value.substring(0, 20) + '...' : value}
                  </span>
                )
              },
              {
                key: 'details',
                label: 'Details',
                render: (value: Record<string, any>) => (
                  <div className="text-sm text-gray-600">
                    {Object.entries(value).slice(0, 2).map(([k, v]) => (
                      <div key={k}>{k}: {String(v)}</div>
                    ))}
                  </div>
                )
              }
            ]}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-500">
            <h3 className="text-lg font-medium">No Events Found</h3>
            <p className="mt-2">No audit events match the selected filters.</p>
          </div>
        </div>
      )}
    </div>
  )
}
