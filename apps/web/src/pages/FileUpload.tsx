import { Helmet } from "react-helmet-async";
import { FileDropzone } from "@/components/FileDropzone";
import { uploadFile } from "@/lib/api";

export default function FileUpload() {
  const onUpload = (category: string) => async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("category", category);
    await uploadFile("/api/v1/files/upload", fd);
  };

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
    </div>
  );
}
