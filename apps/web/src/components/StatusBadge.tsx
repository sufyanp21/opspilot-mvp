import { Badge } from "@/components/ui/badge";

export function StatusBadge({ status }: { status: "RUNNING" | "COMPLETED" | "FAILED" | string }) {
  const s = status.toUpperCase();
  if (s === "COMPLETED") return <Badge className="bg-success text-success-foreground">Completed</Badge>;
  if (s === "FAILED") return <Badge variant="destructive">Failed</Badge>;
  if (s === "RUNNING") return <Badge className="bg-info text-info-foreground">Running</Badge>;
  return <Badge variant="secondary">{status}</Badge>;
}
