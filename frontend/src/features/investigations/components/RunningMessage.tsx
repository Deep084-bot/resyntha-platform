import { Loader2 } from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

export interface RunningMessageProps {
  /**
   * Human-friendly description of what the pipeline is currently doing.
   * Examples: "Retrieving papers", "Validating", "Building landscape".
   */
  phase?: string;
  className?: string;
}

/**
 * Inline replacement for the dashed-border empty state.
 * Shown while an execution is in flight so the user never sees
 * "No papers" / "No artifacts" / "Landscape not yet available".
 */
export function RunningMessage({ phase, className }: RunningMessageProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border bg-surface-hover/30 px-4 py-10",
        className,
      )}
    >
      <Spinner size="md" />
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary">
          {phase ?? "Pipeline is running"}
        </p>
        <p className="mt-1 max-w-sm text-xs text-text-muted">
          Results will appear here as soon as the backend finishes this step.
          This typically takes 1–2 minutes.
        </p>
      </div>
      <span className="sr-only">
        <Loader2 className="h-4 w-4 animate-spin" />
      </span>
    </div>
  );
}
