import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function KPICard({ title, value, delta, hint }: { title: string; value: string | number; delta?: string; hint?: string }) {
  return (
    <Card className="hover-scale shadow-sm" aria-label={`${title} KPI`}>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between">
          <div className="text-3xl font-semibold tracking-tight">{value}</div>
          {delta && (
            <div className="text-sm text-success">{delta}</div>
          )}
        </div>
        {hint && <p className="mt-2 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}
