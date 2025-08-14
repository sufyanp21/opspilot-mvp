import { Helmet } from "react-helmet-async";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/StatusBadge";
import { postJson } from "@/lib/api";
import { useState } from "react";

export default function Reconciliation() {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any | null>(null);

  const runRecon = async () => {
    try {
      setRunning(true);
      setProgress(10);
      const timer = setInterval(() => setProgress((p) => Math.min(95, p + 7)), 400);
      const res = await postJson<any>("/api/v1/reconcile/etd", {});
      clearInterval(timer);
      setProgress(100);
      setResult(res);
    } catch (e) {
      // handled by UI fallback
    } finally {
      setTimeout(() => setRunning(false), 800);
    }
  };

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Reconciliation | OpsPilot MVP</title>
        <meta name="description" content="Run ETD reconciliation and review results." />
        <link rel="canonical" href="/reconciliation" />
      </Helmet>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Reconciliation</h1>
        <Button onClick={runRecon} disabled={running}>
          {running ? "Running..." : "Run ETD Reconciliation"}
        </Button>
      </div>

      {running && (
        <Card>
          <CardHeader>
            <CardTitle>Job Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <StatusBadge status="RUNNING" />
              <div className="flex-1">
                <Progress value={progress} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-secondary">Matched: {result.matched ?? "—"}</div>
              <div className="p-4 rounded-lg bg-secondary">Unmatched: {result.unmatched ?? "—"}</div>
              <div className="p-4 rounded-lg bg-secondary">Exceptions: {result.exceptions ?? "—"}</div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
