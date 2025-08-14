'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

type Exception = { type: string; severity: string; trade_id: string; cluster?: string; details?: any };

export default function ResultsPage() {
  const [internal, setInternal] = useState<File | null>(null);
  const [external, setExternal] = useState<File | null>(null);
  const [data, setData] = useState<{ summary: any; exceptions: Exception[] } | null>(null);
  const [filter, setFilter] = useState<'all' | 'mismatch' | 'missing'>('all');
  const [search, setSearch] = useState('');

  async function runRecon(e: React.FormEvent) {
    e.preventDefault();
    if (!internal || !external) return;
    const fd = new FormData();
    fd.append('internal_csv', internal);
    fd.append('external_csv', external);
    const r = await fetch(`${API_BASE}/reconcile`, { method: 'POST', body: fd });
    const json = await r.json();
    setData(json);
  }

  const filtered = (data?.exceptions || []).filter((ex) => {
    if (filter === 'all') return true;
    if (filter === 'mismatch') return ex.type === 'FIELD_MISMATCH';
    if (filter === 'missing') return ex.type === 'MISSING_INTERNAL' || ex.type === 'MISSING_EXTERNAL';
    return true;
  }).filter((ex) => (search ? ex.trade_id.includes(search) : true));

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Reconciliation Results</h1>
      <form onSubmit={runRecon} className="flex items-center gap-2">
        <input type="file" onChange={(e) => setInternal(e.target.files?.[0] || null)} />
        <input type="file" onChange={(e) => setExternal(e.target.files?.[0] || null)} />
        <button className="px-3 py-1 bg-blue-600 text-white rounded" type="submit">Run</button>
      </form>

      <div className="flex items-center gap-2">
        <span className="text-sm">Filter:</span>
        <select className="border rounded px-2 py-1" value={filter} onChange={(e) => setFilter(e.target.value as any)}>
          <option value="all">All</option>
          <option value="mismatch">Mismatches</option>
          <option value="missing">Missing</option>
        </select>
        <input
          className="border rounded px-2 py-1"
          placeholder="Search trade_id"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {data && (
          <a
            className="ml-auto text-blue-700 underline"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              // CSV export: re-run report endpoint requires paths, so skip in demo
              const lines = [
                'type,severity,trade_id,cluster,details',
                ...(data?.exceptions || []).map((ex) => `${ex.type},${ex.severity},${ex.trade_id},${ex.cluster || ''},"${JSON.stringify(ex.details || {})}"`),
              ];
              const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'exceptions.csv';
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Export CSV
          </a>
        )}
      </div>

      {data && (
        <div className="text-sm text-gray-700">
          <div>Matches: {data.summary.matches}</div>
          <div>Mismatches: {data.summary.mismatches}</div>
          <div>Missing Internal: {data.summary.missing_internal}</div>
          <div>Missing External: {data.summary.missing_external}</div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-2">
        {filtered.map((ex, idx) => (
          <div key={idx} className="border rounded p-3 bg-white">
            <div className="flex gap-4 text-sm">
              <div className="font-mono">{ex.trade_id}</div>
              <div className="px-2 py-0.5 rounded bg-gray-100">{ex.type}</div>
              <div className="ml-auto font-semibold">{ex.severity}</div>
            </div>
            {ex.details && (
              <pre className="mt-2 bg-gray-50 p-2 rounded text-xs overflow-auto">{JSON.stringify(ex.details, null, 2)}</pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


