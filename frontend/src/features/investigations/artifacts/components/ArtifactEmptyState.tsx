import { FlaskConical } from "lucide-react";

export function ArtifactEmptyState() {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border px-4">
      <FlaskConical className="h-8 w-8 text-text-muted" />
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary">
          No artifacts yet
        </p>
        <p className="mt-1 text-xs text-text-muted">
          Artifacts will appear here as the pipeline generates them.
        </p>
      </div>
    </div>
  );
}
