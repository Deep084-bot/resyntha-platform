import { CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  isExecutionTerminal,
  mapExecutionStatus,
  type Execution,
  type ExecutionStage,
} from "@/types";
import { cn } from "@/lib/utils";

export interface InvestigationProgressBannerProps {
  execution: Execution;
  stages: ExecutionStage[];
  className?: string;
}

/**
 * Persistent banner shown above the tabs whenever the latest execution
 * is not terminal. Shows status, current pipeline stage, completed / total
 * stage count, and a real progress bar driven by the stages endpoint.
 *
 * Renders nothing when the latest execution has reached a terminal state
 * (completed / failed / cancelled).
 */
export function InvestigationProgressBanner({
  execution,
  stages,
  className,
}: InvestigationProgressBannerProps) {
  if (isExecutionTerminal(execution.status)) return null;

  const total = stages.length;
  const completed = stages.filter(
    (s) =>
      s.status === "completed" || s.status === "failed" || s.status === "skipped",
  ).length;
  const failed = stages.filter((s) => s.status === "failed").length;

  const currentStage = stages.find((s) => s.status === "running")
    ?? stages.find((s) => s.status === "pending" && s.started_at)
    ?? null;

  const lastCompleted = [...stages]
    .reverse()
    .find((s) => s.status === "completed");

  const phaseLabel = currentStage
    ? prettifyStage(currentStage.stage_name)
    : lastCompleted
      ? prettifyStage(lastCompleted.stage_name)
      : "Starting pipeline";

  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  const isFailed = failed > 0;

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex flex-col gap-3 rounded-lg border bg-surface px-4 py-3",
        isFailed
          ? "border-destructive/30 bg-destructive/5"
          : "border-accent-default/30 bg-accent-default/5",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        {isFailed ? (
          <AlertTriangle className="h-4 w-4 text-destructive" />
        ) : (
          <Spinner size="sm" className="border-t-current" />
        )}
        <span className="font-medium text-text-primary">
          Research is running...
        </span>
        <StatusBadge
          status={mapExecutionStatus(execution.status)}
          label={execution.status}
        />
        <span className="text-text-muted">·</span>
        <span className="text-text-secondary">{phaseLabel}</span>
        <span className="ml-auto text-xs text-text-muted">
          {completed}/{total} stages
          {failed > 0 && (
            <span className="ml-1 text-destructive">({failed} failed)</span>
          )}
        </span>
      </div>

      <div
        className="h-1.5 w-full rounded-full bg-surface-active"
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Investigation pipeline ${percentage}% complete`}
      >
        <div
          className={cn(
            "h-1.5 rounded-full transition-all duration-500",
            isFailed ? "bg-destructive" : "bg-accent-default",
          )}
          style={{ width: `${Math.max(percentage, 4)}%` }}
        />
      </div>

      <span className="sr-only">
        <CheckCircle2 className="h-4 w-4" />
        <Loader2 className="h-4 w-4 animate-spin" />
      </span>
    </div>
  );
}

function prettifyStage(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
