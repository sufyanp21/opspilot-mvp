import { Helmet } from "react-helmet-async";
import { useState } from "react";
import { FileDropzone } from "@/components/FileDropzone";
import { uploadFile } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function OtcProcessing() {
  const [text, setText] = useState("");

  const upload = async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("category", "otc_fpml");
    await uploadFile("/api/v1/files/upload", fd);
  };

  const processText = async () => {
    const blob = new Blob([text], { type: "application/xml" });
    const file = new File([blob], "fpml.xml", { type: "application/xml" });
    await upload(file);
  };

  return (
    <div className="space-y-6">
      <Helmet>
        <title>OTC Processing | OpsPilot MVP</title>
        <meta name="description" content="Process OTC FpML trades via file or paste." />
        <link rel="canonical" href="/otc" />
      </Helmet>

      <h1 className="text-2xl font-semibold">OTC Processing</h1>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        <FileDropzone label="Upload FpML (.xml)" accept=".xml" onUpload={upload} />
        <div className="border rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-2">Paste FpML</p>
          <textarea className="w-full h-40 rounded-md border bg-background p-2" value={text} onChange={(e) => setText(e.target.value)} />
          <div className="mt-2">
            <Button onClick={processText} disabled={!text.trim()}>Process</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
