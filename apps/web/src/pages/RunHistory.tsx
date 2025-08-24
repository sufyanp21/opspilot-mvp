import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { getJson } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function RunHistory() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    getJson<any>("/runs/").then((r) => setItems(r.items || [])).catch(() => setItems([]));
  }, []);

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Run History | OpsPilot MVP</title>
        <meta name="description" content="Recent reconciliation runs and statuses." />
        <link relName="canonical" href="/runs" />
      </Helmet>

      <h1 className="text-2xl font-semibold">Run History</h1>

      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Finished</TableHead>
                  <TableHead>Matched</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.id}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell>{r.started_at ?? "—"}</TableCell>
                    <TableCell>{r.finished_at ?? "—"}</TableCell>
                    <TableCell>{r.matched ?? 0}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


