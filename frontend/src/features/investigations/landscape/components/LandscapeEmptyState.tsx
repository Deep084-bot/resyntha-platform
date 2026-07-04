import { Mountain } from "lucide-react";

export function LandscapeEmptyState() {
  return (
    <div
      className="flex h-64 flex-col items-center justify-center gap-4 rounded-md border border-dashed border-border"
      role="status"
    >
      <Mountain className="h-10 w-10 text-text-muted" />
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary">
          No landscape data yet
        </p>
        <p className="mt-1 text-xs text-text-muted">
          Landscape analysis becomes available after papers are retrieved and
          processed.
        </p>
      </div>
    </div>
  );
}
