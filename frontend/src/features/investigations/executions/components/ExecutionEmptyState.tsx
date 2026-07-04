import { PlayCircle } from "lucide-react";

export function ExecutionEmptyState() {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border px-4">
      <PlayCircle className="h-8 w-8 text-text-muted" />
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary">
          No executions yet
        </p>
        <p className="mt-1 text-xs text-text-muted">
          Run the retrieval pipeline from the Overview tab to get started.
        </p>
      </div>
    </div>
  );
}
