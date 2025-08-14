import { Helmet } from "react-helmet-async";
import { useEffect, useMemo, useState } from "react";
import { getJson } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";

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

  useEffect(() => {
    getJson<ExceptionItem[]>("/api/v1/exceptions/").then(setData).catch(() => {
      setData([
        { id: "EX-101", status: "OPEN", counterparty: "Citi", cluster: "Fees", sla_due_at: "2025-08-18T12:00:00Z" },
        { id: "EX-102", status: "FAILED", counterparty: "JPM", cluster: "Quantities", sla_due_at: "2025-08-12T12:00:00Z" },
        { id: "EX-103", status: "RUNNING", counterparty: "GS", cluster: "Prices", sla_due_at: "2025-08-13T12:00:00Z" },
      ]);
    });
  }, []);

  const filtered = useMemo(() => data.filter(d =>
    [d.id, d.status, d.counterparty, d.cluster].join(" ").toLowerCase().includes(q.toLowerCase())
  ), [data, q]);

  const bulkResolve = () => {
    const ids = Object.keys(selected).filter(k => selected[k]);
    if (!ids.length) return;
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
          <Button variant="secondary" onClick={bulkResolve}>Mark Resolved</Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead></TableHead>
              <TableHead>ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Counterparty</TableHead>
              <TableHead>Cluster</TableHead>
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
                <TableCell><StatusBadge status={e.status} /></TableCell>
                <TableCell>{e.counterparty ?? "—"}</TableCell>
                <TableCell>{e.cluster ?? "—"}</TableCell>
                <TableCell>{e.sla_due_at ? new Date(e.sla_due_at).toLocaleString() : "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
