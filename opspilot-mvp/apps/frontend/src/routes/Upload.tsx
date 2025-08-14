import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileCard from '@/components/FileCard'
import ColumnMapper from '@/components/ColumnMapper'
import { apiClient } from '@/lib/api'
import { FileInfo, ColumnMapping } from '@/lib/types'
import { cn } from '@/lib/utils'

export default function Upload() {
  const navigate = useNavigate()
  const [internalFile, setInternalFile] = useState<FileInfo | null>(null)
  const [clearedFile, setClearedFile] = useState<FileInfo | null>(null)
  const [showColumnMapper, setShowColumnMapper] = useState(false)
  const [columnMapping, setColumnMapping] = useState<ColumnMapping>({
    internal: {},
    cleared: {}
  })
  const [isReconciling, setIsReconciling] = useState(false)

  const handleFileUploaded = (file: FileInfo) => {
    if (file.kind === 'internal') {
      setInternalFile(file)
    } else if (file.kind === 'cleared') {
      setClearedFile(file)
    }

    // Show column mapper when both files are uploaded
    if ((file.kind === 'internal' && clearedFile) || 
        (file.kind === 'cleared' && internalFile)) {
      setShowColumnMapper(true)
    }
  }

  const handleColumnMappingComplete = (mapping: ColumnMapping) => {
    setColumnMapping(mapping)
    setShowColumnMapper(false)
  }

  const runReconciliation = async () => {
    if (!internalFile || !clearedFile) return

    setIsReconciling(true)
    try {
      const result = await apiClient.runReconciliation({
        internal_file_id: internalFile.id,
        cleared_file_id: clearedFile.id,
        column_map: columnMapping,
        match_keys: ['trade_date', 'account', 'symbol'],
        tolerances: {
          price_ticks: 1,
          qty: 0
        }
      })

      // Navigate to reconciliation results
      navigate(`/reconcile/${result.run_id}`)
    } catch (error) {
      console.error('Reconciliation failed:', error)
      alert('Reconciliation failed. Please try again.')
    } finally {
      setIsReconciling(false)
    }
  }

  const canRunReconciliation = internalFile && clearedFile && 
    Object.keys(columnMapping.internal).length > 0 && 
    Object.keys(columnMapping.cleared).length > 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">File Upload</h1>
        <p className="mt-2 text-gray-600">
          Upload internal and cleared trade files to begin reconciliation
        </p>
      </div>

      {/* File Upload Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FileCard
          title="Internal Trades"
          description="Upload your internal trade file (CSV format)"
          fileKind="internal"
          uploadedFile={internalFile}
          onFileUploaded={handleFileUploaded}
        />
        
        <FileCard
          title="Cleared Trades"
          description="Upload your cleared trade file (CSV format)"
          fileKind="cleared"
          uploadedFile={clearedFile}
          onFileUploaded={handleFileUploaded}
        />
      </div>

      {/* Column Mapping */}
      {showColumnMapper && internalFile && clearedFile && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Column Mapping</h2>
          <p className="text-gray-600 mb-4">
            Map the columns from your files to the standard fields
          </p>
          <ColumnMapper
            internalColumns={internalFile.columns || []}
            clearedColumns={clearedFile.columns || []}
            onMappingComplete={handleColumnMappingComplete}
          />
        </div>
      )}

      {/* Reconciliation Button */}
      {internalFile && clearedFile && !showColumnMapper && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Ready to Reconcile</h2>
              <p className="text-gray-600">
                Both files uploaded and columns mapped. Click to start reconciliation.
              </p>
            </div>
            <button
              onClick={runReconciliation}
              disabled={!canRunReconciliation || isReconciling}
              className={cn(
                'px-6 py-3 rounded-md font-medium transition-colors',
                canRunReconciliation && !isReconciling
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              )}
            >
              {isReconciling ? 'Running...' : 'Run Reconciliation'}
            </button>
          </div>
        </div>
      )}

      {/* Status Summary */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-2">Upload Status</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center">
            <span className={cn(
              'w-3 h-3 rounded-full mr-2',
              internalFile ? 'bg-green-500' : 'bg-gray-300'
            )} />
            Internal file: {internalFile ? internalFile.original_name : 'Not uploaded'}
          </div>
          <div className="flex items-center">
            <span className={cn(
              'w-3 h-3 rounded-full mr-2',
              clearedFile ? 'bg-green-500' : 'bg-gray-300'
            )} />
            Cleared file: {clearedFile ? clearedFile.original_name : 'Not uploaded'}
          </div>
          <div className="flex items-center">
            <span className={cn(
              'w-3 h-3 rounded-full mr-2',
              Object.keys(columnMapping.internal).length > 0 ? 'bg-green-500' : 'bg-gray-300'
            )} />
            Column mapping: {Object.keys(columnMapping.internal).length > 0 ? 'Complete' : 'Pending'}
          </div>
        </div>
      </div>
    </div>
  )
}
