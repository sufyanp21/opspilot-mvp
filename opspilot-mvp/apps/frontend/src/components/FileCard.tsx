import { useState, useRef } from 'react'
import { apiClient } from '@/lib/api'
import { FileInfo } from '@/lib/types'
import { cn } from '@/lib/utils'

interface FileCardProps {
  title: string
  description: string
  fileKind: 'internal' | 'cleared' | 'span'
  uploadedFile?: FileInfo | null
  onFileUploaded: (file: FileInfo) => void
}

export default function FileCard({
  title,
  description,
  fileKind,
  uploadedFile,
  onFileUploaded
}: FileCardProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Please upload a CSV file')
      return
    }

    setIsUploading(true)
    try {
      const result = await apiClient.uploadFile(file, fileKind)
      const fileInfo: FileInfo = {
        id: result.file_id,
        kind: fileKind,
        original_name: file.name,
        uploaded_at: new Date().toISOString(),
        processing_status: 'completed',
        columns: result.columns
      }
      onFileUploaded(fileInfo)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const openFileSelector = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-4">{description}</p>

      {uploadedFile ? (
        // File uploaded state
        <div className="border-2 border-green-200 bg-green-50 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm">✓</span>
              </div>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-green-800">
                {uploadedFile.original_name}
              </p>
              <p className="text-sm text-green-600">
                {uploadedFile.columns?.length || 0} columns detected
              </p>
            </div>
          </div>
          <button
            onClick={openFileSelector}
            className="mt-3 text-sm text-green-700 hover:text-green-800 underline"
          >
            Upload different file
          </button>
        </div>
      ) : (
        // Upload area
        <div
          className={cn(
            'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
            dragActive
              ? 'border-blue-400 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400',
            isUploading && 'opacity-50 cursor-not-allowed'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={openFileSelector}
        >
          {isUploading ? (
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-sm text-gray-600">Uploading...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                <span className="text-2xl">📁</span>
              </div>
              <p className="text-sm font-medium text-gray-900">
                Drop your CSV file here, or click to browse
              </p>
              <p className="text-xs text-gray-500 mt-1">CSV files only</p>
            </div>
          )}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleChange}
        className="hidden"
      />
    </div>
  )
}
