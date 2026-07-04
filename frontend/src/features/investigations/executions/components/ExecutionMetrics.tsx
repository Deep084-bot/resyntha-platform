import { Clock, FileText, XCircle, AlertTriangle } from "lucide-react";

import type { Execution, ExecutionStage } from "@/types";

import { formatDuration } from "@/lib/format";

export interface ExecutionMetricsProps {
  execution: Execution;
  stages: ExecutionStage[];
}

export function ExecutionMetrics({
  execution,
  stages,
}: ExecutionMetricsProps) {
  const duration =
    execution.started_at && execution.completed_at
      ? formatDuration(execution.started_at, execution.completed_at)
      : null;

  const succeededStages = stages.filter(
    (s) => s.status === "completed",
  ).length;
  const failedStages = stages.filter((s) => s.status === "failed").length;
  const totalStages = stages.length;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <MetricBox
        icon={Clock}
        label="Duration"
        value={duration ?? "\u2014"}
      />
      <MetricBox
        icon={FileText}
        label="Stages"
        value={`${succeededStages}/${totalStages}`}
      />
      <MetricBox
        icon={XCircle}
        label="Failed"
        value={failedStages}
        highlight={failedStages > 0 ? "destructive" : undefined}
      />
      <MetricBox
        icon={AlertTriangle}
        label="Runs"
        value={
          execution.metadata?.execution_count
            ? String(execution.metadata.execution_count)
            : "1"
        }
      />
    </div>
  );
}

function MetricBox({
  icon: Icon,
  label,
  value,
  highlight,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: React.ReactNode;
  highlight?: "destructive";
}) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border border-border bg-surface-active/50 px-3 py-3 text-center">
      <Icon
        className={
          highlight === "destructive"
            ? "h-4 w-4 text-destructive"
            : "h-4 w-4 text-text-muted"
        }
      />
      <span
        className={
          highlight === "destructive"
            ? "text-lg font-bold text-destructive"
            : "text-lg font-bold text-text-primary"
        }
      >
        {value}
      </span>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  );
}
