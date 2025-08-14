'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function NWayPage() {
  const [internal, setInternal] = useState('[{"trade_id":"T1","product_code":"ES","quantity":1,"price":10}]');
  const [broker, setBroker] = useState('[{"trade_id":"T1","product_code":"ES","quantity":1,"price":10}]');
  const [ccp, setCcp] = useState('[{"trade_id":"T1","product_code":"ES","quantity":1,"price":10}]');
  const [order, setOrder] = useState('[]');
  const [tol, setTol] = useState('{"price":0, "quantity":0}');
  const [res, setRes] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    const payload = {
      internal: JSON.parse(internal),
      broker: JSON.parse(broker),
      ccp: JSON.parse(ccp),
      authoritative_order: (JSON.parse(order)?.length ? JSON.parse(order) : ["ccp","broker","internal"]) as string[],
      tolerances: JSON.parse(tol),
    };
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/reconcile/nway`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
      setRes(await r.json());
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">N-way Reconciliation</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div><div className="text-sm">Internal</div><textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={internal} onChange={(e)=>setInternal(e.target.value)} /></div>
        <div><div className="text-sm">Broker</div><textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={broker} onChange={(e)=>setBroker(e.target.value)} /></div>
        <div><div className="text-sm">CCP</div><textarea className="w-full h-40 border rounded p-2 font-mono text-sm" value={ccp} onChange={(e)=>setCcp(e.target.value)} /></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div><div className="text-sm">Authoritative Order (JSON array)</div><input className="w-full border rounded p-2 font-mono text-sm" value={order} onChange={(e)=>setOrder(e.target.value)} placeholder='["ccp","broker","internal"]' /></div>
        <div><div className="text-sm">Tolerances</div><input className="w-full border rounded p-2 font-mono text-sm" value={tol} onChange={(e)=>setTol(e.target.value)} /></div>
      </div>
      <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={run} disabled={loading}>{loading ? 'Running...' : 'Reconcile'}</button>
      {res && (
        <div className="space-y-2">
          <div className="text-sm">Matches: {res.matches}</div>
          <div className="grid gap-2">
            {(res.exceptions||[]).map((ex:any, i:number) => (
              <div key={i} className="border rounded p-3 bg-white text-sm">
                <div className="flex gap-2 items-center">
                  <div className="font-mono">{ex.trade_id}</div>
                  {ex.authoritative && <span className="px-2 py-0.5 text-xs rounded bg-indigo-100">auth: {ex.authoritative}</span>}
                  <span className="ml-auto">{ex.type}</span>
                </div>
                {ex.details && <pre className="mt-2 bg-gray-50 p-2 rounded text-xs overflow-auto">{JSON.stringify(ex.details, null, 2)}</pre>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


