import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { getJson } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, } from "@/components/ui/card";
import { KPICard } from "@/components/KPICard";

export default function ReconSummary() {
  const [kpis, setKpis] = useState<any | null>(null);
  const [pred, setPred] = useState<any | null>(null);

  useEffect(() => {
    getJson<any>("/runs/DEMO_RUN_1/results").then(setKpis).catch(() => setKpis({ kpis: { matches: 0, mismatches: 0, missing_internal: 0, missing_external: 0 } }));
    getJson<any>("/runs/DEMO_RUN_1/predictions").then(setPred).catch(() => setPred({ items: [] }));
  }, []);

  const counts = pred?.items || [];
  const high = counts.filter((x: any) => x.risk === 'high').length;
  const med = counts.filter((x: any) => x.risk === 'med').length;
  const low = counts.filter((x: any) => x.risk === 'low').length;

  return (
    <div className="space-y-6">
      <Helmet>
        <title>Recon Summary | OpsPilot MVP</title>
      </Helmet>
      <h1 className="text-2xl font-semibold">Reconciliation Summary</h1>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Matches" value={kpis?.kpis?.matches ?? 0} />
        <KPICard title="Mismatches" value={kpis?.kpis?.mismatches ?? 0} />
        <KPICard title="Missing Internal" value={kpis?.kpis?.missing_internal ?? 0} />
        <KPICard title="Missing External" value={kpis?.kpis?.missing_external ?? 0} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Predicted Breaks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
            <KPICard title="High Risk" value={high} />
            <KPICard title="Medium Risk" value={med} />
            <KPICard title="Low Risk" value={low} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


