import { Helmet } from "react-helmet-async";
import { useEffect, useState } from "react";
import { getJson } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface AuditEvent { id: string; type: string; actor?: string; at: string; details?: string }

export default function AuditTrail() {
  const [events, setEvents] = useState<AuditEvent[]>([]);

  useEffect(() => {
    getJson<AuditEvent[]>("/api/v1/audit/events").then(setEvents).catch(() => {
      setEvents([
        { id: "EV-1", type: "UPLOAD", actor: "ops@bank.com", at: new Date().toISOString(), details: "ETD file" },
        { id: "EV-2", type: "RECONCILE", actor: "ops@bank.com", at: new Date().toISOString(), details: "ETD" },
      ]);
    });
  }, []);

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Audit Trail | OpsPilot MVP</title>
        <meta name="description" content="Immutable logs and data lineage." />
        <link rel="canonical" href="/audit" />
      </Helmet>

      <h1 className="text-2xl font-semibold">Audit Trail</h1>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {events.map((e) => (
              <TableRow key={e.id}>
                <TableCell>{e.id}</TableCell>
                <TableCell>{e.type}</TableCell>
                <TableCell>{e.actor ?? "—"}</TableCell>
                <TableCell>{new Date(e.at).toLocaleString()}</TableCell>
                <TableCell>{e.details ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
