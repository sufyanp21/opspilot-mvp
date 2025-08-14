import { Helmet } from "react-helmet-async";
import { useEffect, useState } from "react";
import { getJson } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface SpanRow {
  product: string;
  margin: number;
  deltaNarrative?: string;
}

export default function SpanAnalysis() {
  const [rows, setRows] = useState<SpanRow[]>([]);

  useEffect(() => {
    getJson<SpanRow[]>("/api/v1/span/").then(setRows).catch(() => {
      setRows([
        { product: "ESZ5", margin: 120000, deltaNarrative: "Increase due to volatility spike" },
        { product: "NQZ5", margin: 95000, deltaNarrative: "Decrease after hedge adjustments" },
      ]);
    });
  }, []);

  return (
    <div className="space-y-6">
      <Helmet>
        <title>SPAN Analysis | OpsPilot MVP</title>
        <meta name="description" content="Margin calculations and delta narratives." />
        <link rel="canonical" href="/span" />
      </Helmet>

      <h1 className="text-2xl font-semibold">SPAN Analysis</h1>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Product</TableHead>
              <TableHead>Margin</TableHead>
              <TableHead>Delta Narrative</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.product}>
                <TableCell>{r.product}</TableCell>
                <TableCell>${r.margin.toLocaleString()}</TableCell>
                <TableCell>{r.deltaNarrative ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
