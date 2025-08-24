import { useState } from "react";
import client, { postJson } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PlayCircle, CheckCircle, AlertTriangle, TrendingUp, Activity } from "lucide-react";

export default function Demo() {
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runDemo() {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const { data } = await client.post("/demo/run", {});
      setResult(data);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || err?.response?.data?.detail || "Demo execution failed";
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }

  async function runAutoDemo() {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await postJson("/demo/auto", {});
      setResult(data);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || err?.response?.data?.detail || "Automated demo failed";
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900">Demo Environment</h1>
        <p className="text-slate-600">
          Run a complete reconciliation simulation using sample CME and internal trade data
        </p>
      </div>

      {/* Demo Control */}
      <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl text-blue-900 flex items-center gap-2">
                <PlayCircle className="h-6 w-6" />
                Live Reconciliation Demo
              </CardTitle>
              <CardDescription className="text-blue-700 mt-1">
                Simulates ETD reconciliation with real-world CME position data and internal trades
              </CardDescription>
            </div>
            <Button 
              onClick={runDemo} 
              disabled={isLoading}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : (
                <>
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Run Demo
                </>
              )}
            </Button>
            <Button 
              onClick={runAutoDemo}
              disabled={isLoading}
              size="lg"
              className="ml-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-lg"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Running...
                </>
              ) : (
                <>
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Run Automated Demo
                </>
              )}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Results Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="font-medium">
            Demo Error: {error}
          </AlertDescription>
        </Alert>
      )}

      {result && (
        <div className="space-y-4">
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800 font-medium">
              Demo completed successfully! Reconciliation results are displayed below.
            </AlertDescription>
          </Alert>

          {/* KPI Results */}
          {result.kpis && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Reconciliation Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">{result.kpis.matches}</div>
                    <div className="text-sm text-slate-600 font-medium">Matched Trades</div>
                    <div className="text-xs text-slate-500 mt-1">Perfect reconciliation</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-600">{result.kpis.mismatches}</div>
                    <div className="text-sm text-slate-600 font-medium">Mismatched</div>
                    <div className="text-xs text-slate-500 mt-1">Require investigation</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-red-600">{result.kpis.missing_internal}</div>
                    <div className="text-sm text-slate-600 font-medium">Missing Internal</div>
                    <div className="text-xs text-slate-500 mt-1">Potential trade breaks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{result.kpis.missing_external}</div>
                    <div className="text-sm text-slate-600 font-medium">Missing External</div>
                    <div className="text-xs text-slate-500 mt-1">Settlement discrepancies</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* SPAN Risk Changes */}
          {result.span && result.span.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>SPAN Parameter Changes</CardTitle>
                <CardDescription>Risk parameter deltas detected</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {result.span.map((change: any, index: number) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                      <span className="font-medium">{change.parameter}</span>
                      <span className="text-sm">
                        {change.old_value} → {change.new_value}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Raw JSON Output */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Raw Demo Output</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-slate-100 p-4 rounded text-xs overflow-auto max-h-64">
                {JSON.stringify(result, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Demo Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">What This Demo Does</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-slate-900 mb-2">Data Sources</h4>
              <ul className="space-y-1 text-slate-600">
                <li>• Internal trade positions from book of record</li>
                <li>• CME position data (sample from 2025-08-12)</li>
                <li>• SPAN risk parameter configurations</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-slate-900 mb-2">Reconciliation Process</h4>
              <ul className="space-y-1 text-slate-600">
                <li>• Trade-level matching by product and account</li>
                <li>• Quantity and price variance analysis</li>
                <li>• Exception categorization and clustering</li>
                <li>• Risk parameter change detection</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
