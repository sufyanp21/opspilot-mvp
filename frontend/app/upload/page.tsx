'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function UploadPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [resp, setResp] = useState<any>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files || files.length === 0) return;
    const fd = new FormData();
    Array.from(files).forEach((f) => fd.append('files', f));
    const r = await fetch(`${API_BASE}/upload`, { method: 'POST', body: fd });
    const json = await r.json();
    setResp(json);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Upload Files</h1>
      <form onSubmit={handleSubmit} className="space-y-2">
        <input type="file" multiple onChange={(e) => setFiles(e.target.files)} />
        <button className="px-3 py-1 bg-blue-600 text-white rounded" type="submit">Upload</button>
      </form>
      {resp && (
        <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">{JSON.stringify(resp, null, 2)}</pre>
      )}
    </div>
  );
}


