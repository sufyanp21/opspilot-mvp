import { Helmet } from "react-helmet-async";
import { KPICard } from "@/components/KPICard";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, BarChart, Bar } from "recharts";
import { useEffect, useMemo, useState } from "react";
import { postJson } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { TrendingUp, CheckCircle, AlertTriangle } from "lucide-react";

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

  const [demoResult, setDemoResult] = useState<any>(null);
  const [demoLoading, setDemoLoading] = useState(false);

  const recent = useMemo(() => [
    { id: "EVT-8832", type: "Reconcile", status: "COMPLETED", at: "2m ago" },
    { id: "EVT-8831", type: "Upload", status: "RUNNING", at: "5m ago" },
    { id: "EVT-8829", type: "Exceptions", status: "FAILED", at: "11m ago" },
  ], []);

  async function runDemo() {
    setDemoLoading(true);
    try {
      const result = await postJson("/demo/run", {});
      setDemoResult(result);
    } catch (error) {
      setDemoResult({ error: String(error) });
    } finally {
      setDemoLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Dashboard | OpsPilot MVP</title>
        <meta name="description" content="Real-time KPIs, charts and system status for OpsPilot MVP." />
        <link rel="canonical" href="/" />
      </Helmet>

      <section className="space-y-6">
        {/* Demo Control Center */}
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl text-blue-900">Live Demo Environment</CardTitle>
                <CardDescription className="text-blue-700">
                  Simulate real-time ETD reconciliation with CME sample data
                </CardDescription>
              </div>
              <div className="flex items-center gap-3">
                <Button 
                  onClick={runDemo} 
                  disabled={demoLoading}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg"
                >
                  {demoLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="h-5 w-5 mr-2" />
                      Run Reconciliation Demo
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardHeader>
          {demoResult && (
            <CardContent>
              <div className="rounded-lg p-4 bg-white border">
                {demoResult.error ? (
                  <div className="flex items-center gap-2 text-red-600">
                    <AlertTriangle className="h-5 w-5" />
                    <span className="font-medium">Demo Error:</span>
                    <span>{demoResult.error}</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="h-5 w-5" />
                      <span className="font-medium">Demo Completed Successfully!</span>
                    </div>
                    {demoResult.kpis && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{demoResult.kpis.matches}</div>
                          <div className="text-sm text-gray-600">Matched</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-600">{demoResult.kpis.mismatches}</div>
                          <div className="text-sm text-gray-600">Mismatched</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-red-600">{demoResult.kpis.missing_internal}</div>
                          <div className="text-sm text-gray-600">Missing Internal</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">{demoResult.kpis.missing_external}</div>
                          <div className="text-sm text-gray-600">Missing External</div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          )}
        </Card>

        {/* KPIs */}
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          <KPICard title="Total Trades" value="128,440" delta="+2.3%" hint="last 24h" />
          <KPICard title="Pending Exceptions" value={342} delta="-4.1%" />
          <KPICard title="Margin Utilization" value="68%" />
          <KPICard title="Reconciliation Rate" value="96.4%" />
        </div>
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
