'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function ClustersPage() {
  const [exceptions, setExceptions] = useState('[{"type":"FIELD_MISMATCH","trade_id":"T1","details":{"price":{"internal":10,"external":11}}},{"type":"FIELD_MISMATCH","trade_id":"T2","details":{"price":{"internal":10,"external":11}}}]');
  const [clusters, setClusters] = useState<any[]>([]);

  async function run() {
    const r = await fetch(`${API_BASE}/reconcile/cluster`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ exceptions: JSON.parse(exceptions) }) });
    const json = await r.json();
    setClusters(json.clusters || []);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Break Clusters</h1>
      <textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={exceptions} onChange={(e) => setExceptions(e.target.value)} />
      <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={run}>Cluster</button>
      <div className="grid gap-2">
        {clusters.map((c, i) => (
          <div key={i} className="border rounded p-3 bg-white text-sm">
            <div className="font-semibold">Cluster {c.cluster_id} (size {c.size})</div>
            <ul className="list-disc ml-5">
              {c.members.map((m: any, j: number) => (
                <li key={j}>{m.trade_id} — {m.type}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}


