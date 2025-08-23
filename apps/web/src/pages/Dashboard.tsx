import { Helmet } from "react-helmet-async";
import { KPICard } from "@/components/KPICard";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, BarChart, Bar } from "recharts";
import { useEffect, useMemo, useState } from "react";
import { postJson, getJson } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { TrendingUp, CheckCircle, AlertTriangle, PlayCircle } from "lucide-react";
import { Link } from "react-router-dom";

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
  const [watchlist, setWatchlist] = useState<any>({ top_categories: [], top_products: [] });
  const [weekly, setWeekly] = useState<any>({ weeks: [] });

  const recent = useMemo(() => [
    { id: "EVT-8832", type: "Reconcile", status: "COMPLETED", at: "2m ago" },
    { id: "EVT-8831", type: "Upload", status: "RUNNING", at: "5m ago" },
    { id: "EVT-8829", type: "Exceptions", status: "FAILED", at: "11m ago" },
  ], []);

  useEffect(() => {
    getJson<any>("/benchmark/insights").then((r) => setWatchlist(r)).catch(() => setWatchlist({ top_categories: [], top_products: [] }));
    getJson<any>("/benchmark/insights/weekly").then((r) => setWeekly(r)).catch(() => setWeekly({ weeks: [] }));
  }, []);

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

  async function runAutoDemo() {
    setDemoLoading(true);
    try {
      const result = await postJson("/demo/auto", {});
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

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Overview</h2>
        <div className="flex items-center gap-2">
          <Link to="/demo">
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
              <PlayCircle className="h-4 w-4 mr-2" /> Open Demo
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={runDemo} disabled={demoLoading}>
            {demoLoading ? "Running…" : "Run Demo inline"}
          </Button>
          <Button variant="default" size="sm" onClick={runAutoDemo} disabled={demoLoading}>
            {demoLoading ? "Running…" : "Run Automated Demo"}
          </Button>
        </div>
      </div>

      {/* Automated Demo Output */}
      {demoResult && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle>Automated Demo Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {typeof demoResult.matchRate === "number" && (
              <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
                <KPICard title="Match Rate" value={`${Math.round(demoResult.matchRate * 100)}%`} />
                <KPICard title="OTC Match Rate" value={demoResult.otcMatchRate ? `${Math.round(demoResult.otcMatchRate * 100)}%` : "—"} />
                <KPICard title="Exceptions Sample" value={(demoResult.exceptionsSample?.length || 0).toString()} />
              </div>
            )}
            {Array.isArray(demoResult.exceptionsSample) && demoResult.exceptionsSample.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">Top Exceptions (sample)</h3>
                  <Link to="/exceptions" className="text-blue-600 text-sm">Open Exceptions</Link>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left">
                        {Object.keys(demoResult.exceptionsSample[0]).slice(0,6).map((k) => (
                          <th key={k} className="py-1 pr-4 capitalize">{k}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {demoResult.exceptionsSample.map((row: any, idx: number) => (
                        <tr key={idx} className="border-t">
                          {Object.values(row).slice(0,6).map((v: any, i: number) => (
                            <td key={i} className="py-1 pr-4 whitespace-nowrap">{String(v)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            <pre className="text-[10px] bg-white/60 p-2 rounded max-h-64 overflow-auto">{JSON.stringify(demoResult, null, 2)}</pre>
          </CardContent>
        </Card>
      )}

      <section className="space-y-6">
        {/* Demo Control Center */}
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl text-blue-900">Live Demo Environment</CardTitle>
              </div>
              <div className="flex items-center gap-3">
                <Link to="/demo">
                  <Button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg">
                    <PlayCircle className="h-5 w-5 mr-2" />
                    Go to Demo Page
                  </Button>
                </Link>
                <Link to="/exceptions">
                  <Button variant="outline">Open Exceptions</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
        </Card>
      </section>

      {/* KPIs */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Trades" value="128,440" delta="+2.3%" hint="last 24h" />
        <KPICard title="Pending Exceptions" value={342} delta="-4.1%" />
        <KPICard title="Margin Utilization" value="68%" />
        <KPICard title="Reconciliation Rate" value="96.4%" />
      </div>

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

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Watchlist</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium mb-1">Top Categories</div>
                <ul className="list-disc ml-5">
                  {watchlist.top_categories?.map((x: any) => (
                    <li key={x.category}>{x.category}: {x.count}</li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="font-medium mb-1">Top Products</div>
                <ul className="list-disc ml-5">
                  {watchlist.top_products?.map((x: any) => (
                    <li key={x.product}>{x.product}: {x.count}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-4">
              <div className="font-medium mb-1">Weekly Exceptions</div>
              <div className="grid grid-cols-4 gap-2 text-xs">
                {weekly.weeks?.map((w: any) => (
                  <button
                    key={w.week_start}
                    title={`${w.week_start}: ${w.total}`}
                    className={`h-10 rounded ${w.total>10?'bg-red-300':w.total>5?'bg-yellow-300':'bg-green-300'}`}
                    onClick={() => window.location.href = '/exceptions'}
                  >
                    {w.total}
                  </button>
                ))}
              </div>
            </div>
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

      <section>
        <Card>
          <CardHeader>
            <CardTitle>Help & About</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-3 text-sm">
              <div>
                <div className="font-medium mb-2">Support</div>
                <ul className="space-y-1 list-disc ml-4">
                  <li>
                    <a href="https://support.opspilot.ai" target="_blank" rel="noreferrer" className="text-blue-600 underline">Support Center</a>
                  </li>
                  <li>
                    <a href="https://status.opspilot.ai" target="_blank" rel="noreferrer" className="text-blue-600 underline">Status Page</a>
                  </li>
                  <li>
                    <a href="mailto:support@opspilot.ai" className="text-blue-600 underline">Email Support</a>
                  </li>
                </ul>
              </div>
              <div>
                <div className="font-medium mb-2">FAQs</div>
                <ul className="space-y-1 list-disc ml-4">
                  <li>What is OpsPilot? An AI-first derivatives reconciliation platform.</li>
                  <li>How do I upload data? Use Upload, or run Automated Demo to start.</li>
                  <li>How are predictions explained? SHAP factors and clear rules in UI.</li>
                  <li>Is my data secure? Role-based access, audit trail, SOC2-ready design.</li>
                </ul>
              </div>
              <div>
                <div className="font-medium mb-2">About</div>
                <p>
                  OpsPilot is based in Chicago and focused on the global derivatives
                  ecosystem. We specialize in ETD/OTC reconciliation, SPAN/margin
                  analytics, and exception automation for clearing workflows.
                </p>
                <p className="mt-2 text-muted-foreground">
                  No personal founder identities are exposed in-app. For business
                  inquiries, contact support.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
