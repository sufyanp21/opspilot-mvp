'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

type Step = 1 | 2 | 3;

export default function DemoWizard() {
  const [step, setStep] = useState<Step>(1);
  const [regMode, setRegMode] = useState(false);
  const [tol, setTol] = useState('{"price":0,"quantity":0}');
  const [runSummary, setRunSummary] = useState<any>(null);

  async function runDemo() {
    // Minimal mock: call risk changes + a tiny reconcile with mismatches
    const rc = await fetch(`${API_BASE}/risk/changes`).then((r)=>r.json());
    // Build a pair with mismatch
    const fd = new FormData();
    const csv1 = new Blob(["trade_id,product_code,quantity,price\nT1,ES,1,10\n"], { type: 'text/csv' });
    const csv2 = new Blob(["trade_id,product_code,quantity,price\nT1,ES,2,11\n"], { type: 'text/csv' });
    (fd as any).append('internal_csv', csv1, 'internal.csv');
    (fd as any).append('external_csv', csv2, 'external.csv');
    const recon = await fetch(`${API_BASE}/reconcile`, { method: 'POST', body: fd }).then((r)=>r.json());
    setRunSummary({
      regulatorMode: regMode,
      tolerances: JSON.parse(tol),
      predictedBreaks: 1,
      marginAtRisk:  rc.changes?.length || 0,
      matches: recon.summary?.matches,
      mismatches: recon.summary?.mismatches,
    });
    setStep(3);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Demo Mode</h1>
      {step === 1 && (
        <div className="space-y-3">
          <div className="text-sm">Step 1: Sources</div>
          <div className="text-sm text-gray-700">Using demo CSVs and mocked risk params.</div>
          <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={()=>setStep(2)}>Next</button>
        </div>
      )}
      {step === 2 && (
        <div className="space-y-3">
          <div className="text-sm">Step 2: Tolerances & Regulator Mode</div>
          <div className="flex items-center gap-3">
            <label className="text-sm">Tolerances JSON</label>
            <input className="border rounded px-2 py-1 font-mono text-sm w-full" value={tol} onChange={(e)=>setTol(e.target.value)} />
          </div>
          <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={regMode} onChange={(e)=>setRegMode(e.target.checked)} /> Regulator Mode</label>
          <div className="flex gap-2">
            <button className="px-3 py-1 bg-gray-200 rounded" onClick={()=>setStep(1)}>Back</button>
            <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={runDemo}>Run</button>
          </div>
        </div>
      )}
      {step === 3 && runSummary && (
        <div className="space-y-3">
          <div className="text-sm">Step 3: Results</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="border rounded p-3 bg-white">
              <div className="font-semibold">Matches</div>
              <div>{runSummary.matches}</div>
            </div>
            <div className="border rounded p-3 bg-white">
              <div className="font-semibold">Mismatches</div>
              <div>{runSummary.mismatches}</div>
            </div>
            <div className="border rounded p-3 bg-white">
              <div className="font-semibold">Predicted Breaks</div>
              <div>{runSummary.predictedBreaks}</div>
            </div>
            <div className="border rounded p-3 bg-white">
              <div className="font-semibold">Margin at Risk Signals</div>
              <div>{runSummary.marginAtRisk}</div>
            </div>
          </div>
          <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={()=>setStep(1)}>Restart</button>
        </div>
      )}
    </div>
  );
}


