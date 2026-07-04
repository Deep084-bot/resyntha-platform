import type { Execution, ExecutionStage } from "@/types";
import { isExecutionTerminal } from "@/types";
import { cn } from "@/lib/utils";

export interface ExecutionProgressProps {
  execution: Execution;
  stages: ExecutionStage[];
  className?: string;
}

export function ExecutionProgress({
  execution,
  stages,
  className,
}: ExecutionProgressProps) {
  const totalStages = stages.length;
  const completedStages = stages.filter(
    (s) => s.status === "completed" || s.status === "failed" || s.status === "skipped",
  ).length;
  const failedStages = stages.filter((s) => s.status === "failed").length;
  const isTerminal = isExecutionTerminal(execution.status);

  const percentage =
    totalStages > 0 ? Math.round((completedStages / totalStages) * 100) : 0;

  return (
    <div className={cn("space-y-2", className)}>
      {/* Progress label */}
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-text-primary">
          {isTerminal ? "Completed" : "In Progress"}
        </span>
        <span className="text-xs text-text-muted">
          {completedStages}/{totalStages} stages
          {failedStages > 0 && (
            <span className="ml-1 text-destructive">
              ({failedStages} failed)
            </span>
          )}
        </span>
      </div>

      {/* Progress bar */}
      <div
        className="h-2 w-full rounded-full bg-surface-active"
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Execution ${percentage}% complete`}
      >
        <div
          className={cn(
            "h-2 rounded-full transition-all duration-500",
            failedStages > 0 ? "bg-destructive" : "bg-accent-default",
          )}
          style={{ width: `${Math.max(percentage, 4)}%` }}
        />
      </div>

      {/* Percentage text */}
      <p className="text-xs text-text-muted">{percentage}% complete</p>
    </div>
  );
}
