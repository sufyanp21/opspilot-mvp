'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function RegPackPage() {
  const [records, setRecords] = useState('[{"trade_id":"T1","product_code":"ES","price":10,"quantity":1}]');

  async function exportPack() {
    const r = await fetch(`${API_BASE}/reports/regulatory/export`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ records: JSON.parse(records), lineage: { run_id: 'demo' } }),
    });
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'reg_pack.zip'; a.click(); URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Export Reg Pack</h1>
      <textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={records} onChange={(e) => setRecords(e.target.value)} />
      <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={exportPack}>Export</button>
    </div>
  );
}


