'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function PredictedBreaksPage() {
  const [input, setInput] = useState('[{"trade_id":"T1","quantity":2,"price_dev":0.7},{"trade_id":"T2","quantity":1,"price_dev":0.2}]');
  const [preds, setPreds] = useState<any[]>([]);

  async function run() {
    const r = await fetch(`${API_BASE}/reconciliation/predictions`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: input,
    });
    const json = await r.json();
    setPreds(json.predictions || []);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Predicted Breaks</h1>
      <textarea className="w-full h-32 border rounded p-2 font-mono text-sm" value={input} onChange={(e) => setInput(e.target.value)} />
      <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={run}>Predict</button>
      <div className="grid gap-2">
        {preds.map((p, i) => (
          <div key={i} className="border rounded p-3 bg-white text-sm">
            <div className="flex gap-3"><span className="font-mono">{p.trade_id}</span><span>Prob: {(p.probability*100).toFixed(1)}%</span></div>
            <div>Likely cause: {p.likely_cause}</div>
            <div>Suggested action: {p.suggested_action}</div>
          </div>
        ))}
      </div>
    </div>
  );
}


