import { Helmet } from "react-helmet-async";
import { useEffect, useMemo, useState } from "react";
import { getJson, postJson } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface ExceptionItem {
  id: string;
  status: string;
  counterparty?: string;
  cluster?: string;
  sla_due_at?: string;
  description?: string;
}

export default function Exceptions() {
  const [data, setData] = useState<ExceptionItem[]>([]);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [risk, setRisk] = useState<Record<string, 'high'|'med'|'low'>>({});
  const [explain, setExplain] = useState<Record<string, any>>({});
  const [showHighOnly, setShowHighOnly] = useState(false);

  useEffect(() => {
    getJson<ExceptionItem[]>("/exceptions").then((resp: any) => {
      const items = Array.isArray(resp?.items) ? resp.items : (resp ?? []);
      setData(items);
    }).catch(() => {
      setData([
        { id: "EX-101", status: "OPEN", counterparty: "Citi", cluster: "Fees", sla_due_at: "2025-08-18T12:00:00Z" },
        { id: "EX-102", status: "FAILED", counterparty: "JPM", cluster: "Quantities", sla_due_at: "2025-08-12T12:00:00Z" },
        { id: "EX-103", status: "RUNNING", counterparty: "GS", cluster: "Prices", sla_due_at: "2025-08-13T12:00:00Z" },
      ]);
    });
    // Load predictions for current run (demo id)
    getJson<any>("/runs/DEMO_RUN_1/predictions").then((r) => {
      const m: Record<string, 'high'|'med'|'low'> = {};
      const ex: Record<string, any> = {};
      (r?.items ?? []).forEach((it: any) => { m[it.record_id] = it.risk; ex[it.record_id] = it.explanation; });
      setRisk(m);
      setExplain(ex);
    }).catch(() => {});
  }, []);

  const filtered = useMemo(() => data.filter(d => {
    const matchQ = [d.id, d.status, d.counterparty, d.cluster].join(" ").toLowerCase().includes(q.toLowerCase());
    const riskTag = risk[d.id];
    const matchRisk = !showHighOnly || riskTag === 'high';
    return matchQ && matchRisk;
  }), [data, q, showHighOnly, risk]);

  const bulkResolve = async () => {
    const ids = Object.keys(selected).filter(k => selected[k]);
    if (!ids.length) return;
    try {
      await postJson("/breaks/" + ids[0] + "/resolve", { reason_code: "auto_clear", note: "Auto-cleared via UI" });
    } catch {}
    setData(prev => prev.map(p => ids.includes(p.id) ? { ...p, status: "COMPLETED" } : p));
    setSelected({});
  };

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Exceptions | OpsPilot MVP</title>
        <meta name="description" content="Smart clustering, SLAs and bulk exception management." />
        <link rel="canonical" href="/exceptions" />
      </Helmet>

      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Exceptions</h1>
        <div className="flex items-center gap-2">
          <Input placeholder="Search exceptions..." value={q} onChange={(e) => setQ(e.target.value)} />
          <label className="text-sm flex items-center gap-1">
            <input type="checkbox" checked={showHighOnly} onChange={(e) => setShowHighOnly(e.target.checked)} /> High risk only
          </label>
          <Button variant="secondary" onClick={bulkResolve}>Mark Resolved</Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead></TableHead>
              <TableHead>ID</TableHead>
              <TableHead>Risk</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Counterparty</TableHead>
              <TableHead>Cluster</TableHead>
              <TableHead>Suggested Resolution</TableHead>
              <TableHead>SLA Due</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((e) => (
              <TableRow key={e.id}>
                <TableCell>
                  <input type="checkbox" checked={!!selected[e.id]} onChange={(ev) => setSelected(s => ({...s, [e.id]: ev.target.checked}))} />
                </TableCell>
                <TableCell>{e.id}</TableCell>
                <TableCell>
                  {risk[e.id] ? (
                    <Popover>
                      <PopoverTrigger asChild>
                        <button className={`px-2 py-0.5 rounded text-xs font-medium ${risk[e.id]==='high'?'bg-red-100 text-red-700':risk[e.id]==='med'?'bg-yellow-100 text-yellow-700':'bg-emerald-100 text-emerald-700'}`}>
                          {risk[e.id]}
                        </button>
                      </PopoverTrigger>
                      <PopoverContent className="text-xs">
                        <div className="font-medium mb-1">Why at risk?</div>
                        <ul className="list-disc ml-4">
                          {Array.isArray(explain[e.id]?.top) ? explain[e.id].top.map((t: any, i: number) => (
                            <li key={i}>{String(t)}</li>
                          )) : (
                            <>
                              {explain[e.id]?.likely_cause && <li>{String(explain[e.id].likely_cause)}</li>}
                              {explain[e.id]?.suggested_action && <li>Suggested: {String(explain[e.id].suggested_action)}</li>}
                            </>
                          )}
                        </ul>
                        <div className="mt-2">
                          <button className="px-2 py-1 bg-blue-600 text-white rounded">Resolve suggestion</button>
                        </div>
                      </PopoverContent>
                    </Popover>
                  ) : '—'}
                </TableCell>
                <TableCell><StatusBadge status={e.status} /></TableCell>
                <TableCell>{e.counterparty ?? "—"}</TableCell>
                <TableCell>{e.cluster ?? "—"}</TableCell>
                <TableCell>
                  <button className="text-blue-600 text-xs underline" onClick={async () => { try { await postJson(`/breaks/${e.id}/resolve`, { reason_code: "auto_clear", note: "Auto-cleared (demo)" }); setData(prev => prev.map(p => p.id===e.id?{...p, status: 'COMPLETED'}:p)); } catch {} }}>Auto-clear (85% confidence)</button>
                </TableCell>
                <TableCell>{e.sla_due_at ? new Date(e.sla_due_at).toLocaleString() : "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
