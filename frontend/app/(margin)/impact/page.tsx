'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function MarginImpactPage() {
  const [exceptions, setExceptions] = useState('[{"trade_id":"T1","details":{"price":{"internal":10,"external":11},"quantity":{"internal":1,"external":2}}}]');
  const [span, setSpan] = useState('{"SPAN_SCANNING_RANGE":15.0, "INTERCOMMODITY_CREDIT":0.8}');
  const [result, setResult] = useState<any>(null);

  async function run() {
    const r = await fetch(`${API_BASE}/margin/impact`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ exceptions: JSON.parse(exceptions), span_params: JSON.parse(span) }),
    });
    setResult(await r.json());
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Margin at Risk (24h)</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-sm">Exceptions JSON</div>
          <textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={exceptions} onChange={(e) => setExceptions(e.target.value)} />
        </div>
        <div>
          <div className="text-sm">SPAN Params</div>
          <textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={span} onChange={(e) => setSpan(e.target.value)} />
        </div>
      </div>
      <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={run}>Compute Impact</button>
      {result && (
        <div className="text-sm">
          <div className="font-semibold">Total IM Δ: {result.total_im_delta.toFixed(4)}</div>
          <ul className="list-disc ml-5">
            {result.items.map((it: any, i: number) => (
              <li key={i}>Trade {it.trade_id}: Δ {it.im_delta.toFixed(4)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


