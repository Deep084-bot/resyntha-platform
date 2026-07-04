import { useState } from "react";
import { ChevronDown, ChevronUp, Terminal } from "lucide-react";

import type { ExecutionStage } from "@/types";
import { cn } from "@/lib/utils";

export interface ExecutionLogPreviewProps {
  stages: ExecutionStage[];
  className?: string;
}

export function ExecutionLogPreview({
  stages,
  className,
}: ExecutionLogPreviewProps) {
  const [expanded, setExpanded] = useState(false);

  const logEntries = stages
    .filter((s) => s.error_message || s.status === "running" || s.status === "completed")
    .map((s) => ({
      id: s.id,
      timestamp: s.started_at,
      stage: s.stage_name,
      message:
        s.error_message ??
        (s.status === "running"
          ? `${s.stage_name} stage is running...`
          : s.status === "completed"
            ? `${s.stage_name} completed successfully.`
            : ""),
      level: s.error_message ? "error" : "info" as "error" | "info",
    }));

  if (logEntries.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
        <p className="text-xs text-text-muted">No log entries available.</p>
      </div>
    );
  }

  const visibleEntries = expanded ? logEntries : logEntries.slice(-5);

  return (
    <div className={cn("space-y-2", className)}>
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider flex items-center gap-1.5">
        <Terminal className="h-3 w-3" />
        Logs
      </h3>
      <div className="rounded-md border border-border bg-surface-active/50 font-mono text-xs">
        {visibleEntries.map((entry) => (
          <div
            key={entry.id}
            className={cn(
              "flex gap-2 border-b border-border/50 px-3 py-1.5 last:border-0",
              entry.level === "error" && "bg-destructive/5",
            )}
          >
            <span className="shrink-0 text-text-muted">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span
              className={cn(
                entry.level === "error"
                  ? "text-destructive"
                  : "text-text-secondary",
              )}
            >
              {entry.message}
            </span>
          </div>
        ))}
        {logEntries.length > 5 && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex w-full items-center justify-center gap-1 px-3 py-2 text-text-muted hover:text-text-primary transition-colors"
            aria-expanded={expanded}
            aria-label={expanded ? "Show fewer logs" : "Show all logs"}
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3 w-3" />
                Show fewer
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" />
                Show all ({logEntries.length} entries)
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
