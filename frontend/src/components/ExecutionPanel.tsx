import { cn } from "@/lib/utils";
import { Clock } from "lucide-react";
import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatDateTime, formatDuration } from "@/lib/format";
import { mapExecutionStatus, type Execution } from "@/types";

interface ExecutionPanelProps {
  executions: Execution[] | undefined;
  isLoading: boolean;
  onSelect?: (id: string) => void;
  selectedId?: string;
  emptyAction?: ReactNode;
}

export function ExecutionPanel({ executions, isLoading, onSelect, selectedId, emptyAction }: ExecutionPanelProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!executions || executions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border py-8">
        <p className="text-sm text-text-muted">
          No executions yet. Run the retrieval pipeline to create one.
        </p>
        {emptyAction}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {executions.map((exe) => (
        <button
          key={exe.id}
          type="button"
          onClick={() => onSelect?.(exe.id)}
          className={cn(
            "flex w-full items-center gap-4 rounded-lg border px-4 py-3 text-left transition-colors",
            selectedId === exe.id
              ? "border-accent-default/40 bg-accent-default/5"
              : "border-border bg-surface-card hover:bg-surface-active",
          )}
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-active">
            <Clock className="h-4 w-4 text-text-secondary" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-text-primary font-mono">
                {exe.id.slice(0, 8)}
              </span>
              <StatusBadge
                status={mapExecutionStatus(exe.status)}
                label={exe.status}
              />
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
              <span>Trigger: {exe.trigger}</span>
              {exe.started_at && (
                <span>Started: {formatDateTime(exe.started_at)}</span>
              )}
              {exe.completed_at && (
                <span>Duration: {formatDuration(exe.started_at, exe.completed_at)}</span>
              )}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
