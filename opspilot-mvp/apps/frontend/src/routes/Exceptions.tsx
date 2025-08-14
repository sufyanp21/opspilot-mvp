import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { apiClient } from '@/lib/api'
import { ExceptionInfo } from '@/lib/types'
import { formatDateTime } from '@/lib/utils'
import DataGrid from '@/components/DataGrid'

export default function Exceptions() {
  const [exceptions, setExceptions] = useState<ExceptionInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedException, setSelectedException] = useState<ExceptionInfo | null>(null)
  const [filterStatus, setFilterStatus] = useState<'all' | 'OPEN' | 'RESOLVED'>('all')
  
  // Work Order 4: Exception clustering and SLA workflow state
  const [clusters, setClusters] = useState<any[]>([])
  const [slaBreaches, setSlaBreaches] = useState<any[]>([])
  const [teams, setTeams] = useState<any[]>([])
  const [selectedExceptions, setSelectedExceptions] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState('exceptions')
  const [clusteringLoading, setClusteringLoading] = useState(false)
  const [assignmentLoading, setAssignmentLoading] = useState(false)

  useEffect(() => {
    loadExceptions()
    loadTeams()
    loadSlaBreaches()
  }, [])

  // Work Order 4: Load clustering and SLA data
  const loadTeams = async () => {
    try {
      const response = await fetch('/api/v1/exceptions/filters/teams')
      const data = await response.json()
      setTeams(data.teams || [])
    } catch (error) {
      console.error('Failed to load teams:', error)
    }
  }

  const loadSlaBreaches = async () => {
    try {
      const response = await fetch('/api/v1/exceptions/sla-breaches')
      const data = await response.json()
      setSlaBreaches(data || [])
    } catch (error) {
      console.error('Failed to load SLA breaches:', error)
    }
  }

  const runClustering = async () => {
    setClusteringLoading(true)
    try {
      const response = await fetch('/api/v1/exceptions/cluster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enable_exact_matching: true,
          enable_fuzzy_matching: true,
          min_cluster_size: 2
        })
      })
      const clusterData = await response.json()
      setClusters(clusterData || [])
    } catch (error) {
      console.error('Failed to run clustering:', error)
    } finally {
      setClusteringLoading(false)
    }
  }

  const bulkAssign = async (teamId: string) => {
    if (selectedExceptions.size === 0) return
    
    setAssignmentLoading(true)
    try {
      const response = await fetch('/api/v1/exceptions/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exception_ids: Array.from(selectedExceptions),
          team_id: teamId,
          assigned_by: 'user_frontend',
          notes: 'Bulk assignment from frontend'
        })
      })
      
      if (response.ok) {
        setSelectedExceptions(new Set())
        loadExceptions() // Refresh data
      }
    } catch (error) {
      console.error('Failed to bulk assign:', error)
    } finally {
      setAssignmentLoading(false)
    }
  }

  const toggleExceptionSelection = (exceptionId: string) => {
    const newSelection = new Set(selectedExceptions)
    if (newSelection.has(exceptionId)) {
      newSelection.delete(exceptionId)
    } else {
      newSelection.add(exceptionId)
    }
    setSelectedExceptions(newSelection)
  }

  const loadExceptions = async () => {
    setLoading(true)
    try {
      // For demo purposes, we'll load exceptions from the most recent run
      const runs = await apiClient.listReconciliationRuns()
      if (runs.length > 0) {
        const latestRun = runs[0]
        const exceptionsData = await apiClient.getRunExceptions(latestRun.id)
        setExceptions(exceptionsData)
      }
    } catch (error) {
      console.error('Failed to load exceptions:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredExceptions = exceptions.filter(exc => 
    filterStatus === 'all' || exc.status === filterStatus
  )

  const handleRowClick = (exception: ExceptionInfo) => {
    setSelectedException(exception)
  }

  const closeDrawer = () => {
    setSelectedException(null)
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Exception Management</h1>
          <p className="mt-2 text-gray-600">
            Advanced exception clustering, SLA tracking, and bulk operations
          </p>
        </div>
        
        {/* Bulk Actions */}
        {selectedExceptions.size > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">{selectedExceptions.size} selected</span>
            <select
              onChange={(e) => e.target.value && bulkAssign(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              disabled={assignmentLoading}
            >
              <option value="">Assign to Team...</option>
              {teams.map((team: any) => (
                <option key={team.team_id} value={team.team_id}>
                  {team.team_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Work Order 4: Tabbed Interface */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'exceptions', label: 'All Exceptions', count: exceptions.length },
              { id: 'clusters', label: 'Clusters', count: clusters.length },
              { id: 'sla', label: 'SLA Breaches', count: slaBreaches.length },
              { id: 'teams', label: 'Team Workload', count: teams.length }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                    activeTab === tab.id ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'exceptions' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">All Exceptions</h3>
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium text-gray-700">Filter:</label>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value as any)}
                    className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="all">All Status</option>
                    <option value="OPEN">Open</option>
                    <option value="RESOLVED">Resolved</option>
                  </select>
                </div>
              </div>

              {/* Exception Grid with Checkboxes */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedExceptions(new Set(filteredExceptions.map(exc => exc.id)))
                            } else {
                              setSelectedExceptions(new Set())
                            }
                          }}
                          className="rounded border-gray-300"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Keys</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Differences</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SLA</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Team</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredExceptions.map((exception) => (
                      <tr key={exception.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedExceptions.has(exception.id)}
                            onChange={() => toggleExceptionSelection(exception.id)}
                            className="rounded border-gray-300"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            exception.status === 'OPEN' 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {exception.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {Object.entries(exception.keys).slice(0, 2).map(([k, v]) => (
                            <div key={k}>{k}: {v}</div>
                          ))}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {exception.diff ? Object.keys(exception.diff).length + ' fields' : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                            MEDIUM
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          Operations
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'clusters' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Exception Clusters</h3>
                <button
                  onClick={runClustering}
                  disabled={clusteringLoading}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {clusteringLoading ? 'Clustering...' : 'Run Clustering'}
                </button>
              </div>

              {clusters.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No clusters found. Click "Run Clustering" to analyze exceptions.
                </div>
              ) : (
                <div className="grid gap-4">
                  {clusters.map((cluster) => (
                    <div key={cluster.cluster_id} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">
                          Cluster: {cluster.probable_cause}
                        </h4>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            cluster.severity_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                            cluster.severity_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                            cluster.severity_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {cluster.severity_level}
                          </span>
                          <span className="text-sm text-gray-500">
                            {cluster.exception_count} exceptions
                          </span>
                        </div>
                      </div>
                      <div className="text-sm text-gray-600">
                        <p>Method: {cluster.clustering_method}</p>
                        <p>Accounts: {cluster.accounts_affected.join(', ')}</p>
                        <p>Products: {cluster.products_affected.join(', ')}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'sla' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">SLA Breaches</h3>
              
              {slaBreaches.length === 0 ? (
                <div className="text-center py-8 text-green-600">
                  🎉 No SLA breaches! All exceptions are within SLA targets.
                </div>
              ) : (
                <div className="space-y-3">
                  {slaBreaches.map((breach) => (
                    <div key={breach.assignment_id} className="border-l-4 border-red-400 bg-red-50 p-4 rounded">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-red-800">
                            Exception {breach.exception_id}
                          </h4>
                          <p className="text-sm text-red-600">
                            {breach.hours_overdue.toFixed(1)} hours overdue
                          </p>
                          <p className="text-xs text-red-500">
                            Assigned to: {breach.assigned_team_id}
                          </p>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            breach.sla_severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                            breach.sla_severity === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {breach.sla_severity}
                          </span>
                          {breach.is_escalated && (
                            <span className="ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                              ESCALATED
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'teams' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Team Workload</h3>
              
              <div className="grid gap-4">
                {teams.map((team) => (
                  <div key={team.team_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">{team.team_name}</h4>
                      <span className="text-sm text-gray-500">{team.team_type}</span>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Capacity</p>
                        <p className="font-medium">{team.capacity}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Current Load</p>
                        <p className="font-medium">0</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Utilization</p>
                        <p className="font-medium">0%</p>
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      <p className="text-sm text-gray-500 mb-1">Specializations:</p>
                      <div className="flex flex-wrap gap-1">
                        {team.specializations.map((spec: string) => (
                          <span key={spec} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                            {spec}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">⚠️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Open Exceptions</p>
              <p className="text-2xl font-bold text-gray-900">
                {exceptions.filter(e => e.status === 'OPEN').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">✅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Resolved</p>
              <p className="text-2xl font-bold text-gray-900">
                {exceptions.filter(e => e.status === 'RESOLVED').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0 w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <span className="text-xl">📊</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total</p>
              <p className="text-2xl font-bold text-gray-900">{exceptions.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Exceptions Table */}
      {filteredExceptions.length > 0 ? (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Exceptions ({filteredExceptions.length})
            </h2>
          </div>
          <DataGrid
            data={filteredExceptions}
            columns={[
              {
                key: 'id',
                label: 'ID',
                render: (value: string) => value.substring(0, 8) + '...'
              },
              {
                key: 'status',
                label: 'Status',
                render: (value: string) => (
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    value === 'OPEN' 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {value}
                  </span>
                )
              },
              {
                key: 'keys',
                label: 'Match Keys',
                render: (value: Record<string, any>) => (
                  <div className="text-sm">
                    {Object.entries(value).slice(0, 2).map(([k, v]) => (
                      <div key={k}>{k}: {v}</div>
                    ))}
                  </div>
                )
              },
              {
                key: 'diff',
                label: 'Issue Type',
                render: (value: Record<string, any>) => {
                  if (value?.status === 'missing_in_cleared') return 'Missing in Cleared'
                  if (value?.status === 'missing_in_internal') return 'Missing in Internal'
                  if (value?.price_ticks) return 'Price Difference'
                  if (value?.qty) return 'Quantity Difference'
                  return 'Other'
                }
              }
            ]}
            onRowClick={handleRowClick}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-500">
            <h3 className="text-lg font-medium">No Exceptions Found</h3>
            <p className="mt-2">
              {filterStatus === 'all' 
                ? 'No exceptions to display. Run a reconciliation to see results.'
                : `No ${filterStatus.toLowerCase()} exceptions found.`
              }
            </p>
          </div>
        </div>
      )}

      {/* Exception Detail Drawer */}
      {selectedException && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={closeDrawer} />
          <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-xl">
            <div className="flex flex-col h-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Exception Details</h3>
                  <button
                    onClick={closeDrawer}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Match Keys</h4>
                  <div className="bg-gray-50 p-3 rounded text-sm">
                    {Object.entries(selectedException.keys).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="font-medium">{k}:</span>
                        <span>{v}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedException.internal && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Internal Data</h4>
                    <div className="bg-blue-50 p-3 rounded text-sm">
                      {Object.entries(selectedException.internal).slice(0, 5).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="font-medium">{k}:</span>
                          <span>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedException.cleared && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Cleared Data</h4>
                    <div className="bg-green-50 p-3 rounded text-sm">
                      {Object.entries(selectedException.cleared).slice(0, 5).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="font-medium">{k}:</span>
                          <span>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedException.diff && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Differences</h4>
                    <div className="bg-red-50 p-3 rounded text-sm">
                      {Object.entries(selectedException.diff).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="font-medium">{k}:</span>
                          <span className="text-red-600">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="px-6 py-4 border-t border-gray-200">
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Resolution Notes
                    </label>
                    <textarea
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      rows={3}
                      placeholder="Add notes about the resolution..."
                    />
                  </div>
                  <div className="flex space-x-3">
                    <button className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors">
                      Mark Resolved
                    </button>
                    <button className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition-colors">
                      Save Notes
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
