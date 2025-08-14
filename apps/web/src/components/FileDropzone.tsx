import { useCallback, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/hooks/use-toast";

export function FileDropzone({ label, accept, onUpload }: { label: string; accept: string; onUpload: (file: File) => Promise<void> }) {
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || !files.length) return;
    const file = files[0];
    setLoading(true);
    setProgress(10);
    try {
      await onUpload(file);
      setProgress(100);
      toast({ title: `${label} uploaded`, description: `${file.name} uploaded successfully.` });
    } catch (e: any) {
      toast({ title: `Upload failed`, description: e?.message ?? "An error occurred", variant: "destructive" as any });
    } finally {
      setTimeout(() => setProgress(0), 1000);
      setLoading(false);
    }
  }, [label, onUpload]);

  return (
    <div
      className={`border rounded-lg p-6 text-center transition-colors ${dragOver ? "bg-muted" : "bg-card"}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
    >
      <p className="mb-2 text-sm text-muted-foreground">{label}</p>
      <input
        type="file"
        accept={accept}
        onChange={(e) => handleFiles(e.target.files)}
        className="mx-auto block"
      />
      {loading && (
        <div className="mt-4">
          <Progress value={progress} aria-label="Upload progress" />
        </div>
      )}
    </div>
  );
}
