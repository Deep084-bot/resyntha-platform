import { Clock } from "lucide-react";

import type { Execution } from "@/types";
import { ExecutionStatusBadge } from "./ExecutionStatusBadge";
import { formatDateTime, formatDuration } from "@/lib/format";

export interface ExecutionHistoryProps {
  executions: Execution[];
  selectedId: string | undefined;
  onSelect: (id: string) => void;
}

export function ExecutionHistory({
  executions,
  selectedId,
  onSelect,
}: ExecutionHistoryProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
        History
      </h3>
      <div className="space-y-2">
        {executions.map((exe) => (
          <button
            key={exe.id}
            type="button"
            onClick={() => onSelect(exe.id)}
            className={`flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
              selectedId === exe.id
                ? "border-accent-default/40 bg-accent-default/5"
                : "border-border bg-surface-card hover:bg-surface-active"
            }`}
            aria-pressed={selectedId === exe.id}
            aria-label={`Execution ${exe.id.slice(0, 8)} (${exe.status})`}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-active">
              <Clock className="h-4 w-4 text-text-secondary" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary font-mono">
                  {exe.id.slice(0, 8)}
                </span>
                <ExecutionStatusBadge status={exe.status} />
              </div>
              <div className="mt-0.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
                <span>Trigger: {exe.trigger}</span>
                {exe.started_at && (
                  <span>Started: {formatDateTime(exe.started_at)}</span>
                )}
                {exe.completed_at && (
                  <span>
                    Duration: {formatDuration(exe.started_at, exe.completed_at)}
                  </span>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
