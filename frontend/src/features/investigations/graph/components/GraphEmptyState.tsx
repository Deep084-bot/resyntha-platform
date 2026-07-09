import { Share2 } from "lucide-react";

export function GraphEmptyState() {
  return (
    <div
      className="flex h-64 flex-col items-center justify-center gap-4 rounded-md border border-dashed border-border"
      role="status"
    >
      <Share2 className="h-10 w-10 text-text-muted" />
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary">
          Research graph will appear once the investigation finishes.
        </p>
        <p className="mt-1 text-xs text-text-muted">
          Run an investigation to generate extracted knowledge and explore relationships.
        </p>
      </div>
    </div>
  );
}
