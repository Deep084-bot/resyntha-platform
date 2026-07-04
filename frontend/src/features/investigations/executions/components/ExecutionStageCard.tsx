import { CheckCircle2, XCircle, Clock, Play, SkipForward } from "lucide-react";

import type { ExecutionStage, ExecutionStageStatus } from "@/types";
import { formatDuration } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface ExecutionStageCardProps {
  stage: ExecutionStage;
  isLast?: boolean;
}

const STATUS_CONFIG: Record<
  ExecutionStageStatus,
  {
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    label: string;
  }
> = {
  pending: { icon: Clock, color: "text-text-muted", label: "Pending" },
  running: { icon: Play, color: "text-accent-default", label: "Running" },
  completed: { icon: CheckCircle2, color: "text-success", label: "Completed" },
  failed: { icon: XCircle, color: "text-destructive", label: "Failed" },
  skipped: { icon: SkipForward, color: "text-text-muted", label: "Skipped" },
};

export function ExecutionStageCard({
  stage,
  isLast,
}: ExecutionStageCardProps) {
  const config = STATUS_CONFIG[stage.status];
  const Icon = config.icon;

  return (
    <div className="relative flex gap-4">
      {/* Vertical connector line */}
      {!isLast && (
        <div className="absolute left-[15px] top-8 bottom-0 w-px bg-border" />
      )}

      {/* Status icon */}
      <div className="relative z-10 flex shrink-0 items-start pt-0.5">
        <div
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-full border-2",
            stage.status === "completed"
              ? "border-success bg-success/10"
              : stage.status === "failed"
                ? "border-destructive bg-destructive/10"
                : stage.status === "running"
                  ? "border-accent-default bg-accent-default/10"
                  : "border-border bg-surface-active",
          )}
        >
          {stage.status === "running" ? (
            <span className="flex h-2 w-2">
              <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-accent-default opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-default" />
            </span>
          ) : (
            <Icon className={cn("h-3.5 w-3.5", config.color)} />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-6">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-medium text-text-primary capitalize">
              {stage.stage_name.replace(/_/g, " ")}
            </span>
            {stage.attempt > 1 && (
              <span className="rounded bg-warning/10 px-1 py-0.5 text-[10px] font-medium text-warning">
                Attempt {stage.attempt}
              </span>
            )}
          </div>
          {stage.duration_ms != null && (
            <span className="shrink-0 text-xs text-text-muted">
              {formatDuration(stage.started_at, stage.completed_at ?? stage.started_at)}
            </span>
          )}
        </div>

        {/* Timestamps */}
        <div className="mt-0.5 flex items-center gap-3 text-xs text-text-muted">
          <span>Started {new Date(stage.started_at).toLocaleTimeString()}</span>
          {stage.completed_at && (
            <span>
              Finished {new Date(stage.completed_at).toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Error message */}
        {stage.error_message && (
          <div className="mt-2 rounded-md bg-destructive/5 border border-destructive/20 px-3 py-2">
            <p className="text-xs text-destructive">{stage.error_message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
