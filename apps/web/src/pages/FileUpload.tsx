import { Helmet } from "react-helmet-async";
import { FileDropzone } from "@/components/FileDropzone";
import { uploadFile, postJson, getJson } from "@/lib/api";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function FileUpload() {
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [sourceId, setSourceId] = useState<string>("demo-cme");

  const onUpload = (category: string) => async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("category", category);
    await uploadFile("/ingestion/files", file, { category });
    // Parse CSV headers client-side (quick peek)
    if (file.name.endsWith('.csv')) {
      const text = await file.text();
      const firstLine = text.split(/\r?\n/)[0] || "";
      const cols = firstLine.split(",").map((s) => s.trim()).filter(Boolean).slice(0, 20);
      setHeaders(cols);
    }
  };

  const canonical = [
    "trade_id","product_code","account","quantity","price","notional","currency","valuation_ts"
  ];

  async function saveMapping() {
    await postJson("/ingestion/mappings", { source_id: sourceId, name: `auto-${new Date().toISOString()}`, mapping });
  }

  return (
    <div className="space-y-6">
      <Helmet>
        <title>File Upload | OpsPilot MVP</title>
        <meta name="description" content="Upload ETD, SPAN and OTC FpML files for processing." />
        <link rel="canonical" href="/upload" />
      </Helmet>

      <h1 className="text-2xl font-semibold">File Upload</h1>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <FileDropzone label="ETD Trades (.csv, .xlsx)" accept=".csv,.xlsx" onUpload={onUpload("etd_trades")} />
        <FileDropzone label="SPAN Margins (.csv)" accept=".csv" onUpload={onUpload("span_margins")} />
        <FileDropzone label="OTC FpML (.xml)" accept=".xml" onUpload={onUpload("otc_fpml")} />
      </div>

      {headers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Map Columns (source: {sourceId})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {headers.map((h) => (
                <div key={h} className="flex items-center gap-2">
                  <div className="w-1/2 text-sm">{h}</div>
                  <select
                    className="w-1/2 border rounded px-2 py-1 text-sm"
                    value={mapping[h] || ""}
                    onChange={(e) => setMapping((m) => ({ ...m, [h]: e.target.value }))}
                  >
                    <option value="">– map to –</option>
                    {canonical.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
            <div className="mt-4 flex gap-2">
              <Button onClick={saveMapping}>Save Mapping</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
