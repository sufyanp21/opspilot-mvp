'use client';

import useSWR from 'swr';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function RiskChangesPage() {
  const { data } = useSWR(`${API_BASE}/risk/changes`, fetcher);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Risk Changes</h1>
      {!data && <div>Loading...</div>}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.changes.map((c: any) => (
            <div key={c.param} className="border rounded p-3 bg-white">
              <div className="font-semibold">{c.param}</div>
              <div className="text-sm text-gray-700">Old: {String(c.old)} → New: {String(c.new)}</div>
              <div className="text-sm">Δ: {String(c.delta)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


