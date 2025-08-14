import { Helmet } from "react-helmet-async";
import { KPICard } from "@/components/KPICard";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, BarChart, Bar } from "recharts";
import { useEffect, useMemo, useState } from "react";

const genData = () => Array.from({ length: 12 }).map((_, i) => ({ name: `T${i+1}`, value: Math.round(70 + Math.random()*30) }))

export default function Dashboard() {
  const [reconData, setReconData] = useState(genData());
  const [excData, setExcData] = useState(Array.from({ length: 8 }).map((_, i) => ({ name: `W${i+1}`, value: Math.round(10 + Math.random()*30) })));

  useEffect(() => {
    const id = setInterval(() => {
      setReconData(genData());
    }, 5000);
    return () => clearInterval(id);
  }, []);

  const recent = useMemo(() => [
    { id: "EVT-8832", type: "Reconcile", status: "COMPLETED", at: "2m ago" },
    { id: "EVT-8831", type: "Upload", status: "RUNNING", at: "5m ago" },
    { id: "EVT-8829", type: "Exceptions", status: "FAILED", at: "11m ago" },
  ], []);

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Dashboard | OpsPilot MVP</title>
        <meta name="description" content="Real-time KPIs, charts and system status for OpsPilot MVP." />
        <link rel="canonical" href="/" />
      </Helmet>

      <section className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Trades" value="128,440" delta="+2.3%" hint="last 24h" />
        <KPICard title="Pending Exceptions" value={342} delta="-4.1%" />
        <KPICard title="Margin Utilization" value="68%" />
        <KPICard title="Reconciliation Rate" value="96.4%" />
      </section>

      <section className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Reconciliation Progress</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={reconData}>
                <XAxis dataKey="name" />
                <YAxis domain={[60, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Exception Trends</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={excData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="hsl(var(--destructive))" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recent.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.id}</TableCell>
                    <TableCell>{r.type}</TableCell>
                    <TableCell><StatusBadge status={r.status} /></TableCell>
                    <TableCell>{r.at}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
