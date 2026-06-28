import { useState } from "react";
import { useParams } from "react-router-dom";
import { AlertCircle, CheckCircle2, Clock, SkipForward } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PipelineStageCard } from "@/components/ui/pipeline-stage-card";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ExecutionPanel } from "@/components/ExecutionPanel";
import { useExecutionStages, useExecutions } from "@/hooks/useExecutions";
import { formatDateTime, formatDuration } from "@/lib/format";
import { mapExecutionStatus, mapStageStatus, type Execution, type ExecutionStage } from "@/types";

function StageTimeline({ stages }: { stages: ExecutionStage[] }) {
  return (
    <div className="space-y-2">
      {stages.map((s) => (
        <PipelineStageCard
          key={s.id}
          name={s.stage_name}
          description={
            s.error_message
              ? s.error_message
              : s.status === "skipped"
                ? "Stage was skipped"
                : `Attempt ${s.attempt}`
          }
          status={mapStageStatus(s.status)}
          duration={
            s.duration_ms != null
              ? `${(s.duration_ms / 1000).toFixed(1)}s`
              : s.status === "running"
                ? "Running..."
                : undefined
          }
          isActive={s.status === "running"}
        />
      ))}
    </div>
  );
}

function ExecutionMonitor({ execution }: { execution: Execution }) {
  const { data: stages, isLoading: stagesLoading } = useExecutionStages(execution.id);
  const isTerminal = execution.status === "completed" || execution.status === "failed" || execution.status === "cancelled";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span className="font-mono text-sm">{execution.id.slice(0, 8)}</span>
          <StatusBadge
            status={mapExecutionStatus(execution.status)}
            label={execution.status}
          />
          {execution.started_at && execution.completed_at && (
            <span className="text-sm font-normal text-text-muted">
              {formatDuration(execution.started_at, execution.completed_at)}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-text-muted">Trigger: </span>
            <span className="text-text-primary">{execution.trigger}</span>
          </div>
          <div>
            <span className="text-text-muted">Created by: </span>
            <span className="text-text-primary">{execution.created_by ?? "\u2014"}</span>
          </div>
          {execution.started_at && (
            <div>
              <span className="text-text-muted">Started: </span>
              <span className="text-text-primary">{formatDateTime(execution.started_at)}</span>
            </div>
          )}
          {execution.completed_at && (
            <div>
              <span className="text-text-muted">Completed: </span>
              <span className="text-text-primary">{formatDateTime(execution.completed_at)}</span>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-text-primary">Stages</h4>
          {stagesLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded-lg" />
              ))}
            </div>
          ) : stages && stages.length > 0 ? (
            <StageTimeline stages={stages} />
          ) : isTerminal ? (
            <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
              <p className="text-sm text-text-muted">No stage data recorded for this execution.</p>
            </div>
          ) : (
            <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
              <p className="text-sm text-text-muted">Waiting for stage data...</p>
            </div>
          )}
        </div>

        {/* Stats summary */}
        {stages && stages.length > 0 && (
          <div className="mt-4 grid grid-cols-4 gap-3 border-t border-border pt-4">
            <StatBox
              icon={CheckCircle2}
              label="Succeeded"
              count={stages.filter((s) => s.status === "completed").length}
              color="text-success"
            />
            <StatBox
              icon={AlertCircle}
              label="Failed"
              count={stages.filter((s) => s.status === "failed").length}
              color="text-destructive"
            />
            <StatBox
              icon={SkipForward}
              label="Skipped"
              count={stages.filter((s) => s.status === "skipped").length}
              color="text-text-muted"
            />
            <StatBox
              icon={Clock}
              label="Retries"
              count={stages.filter((s) => s.attempt > 1).length}
              color="text-warning"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StatBox({
  icon: Icon,
  label,
  count,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  count: number;
  color: string;
}) {
  return (
    <div className="flex flex-col items-center gap-1 text-center">
      <Icon className={`h-4 w-4 ${color}`} />
      <span className="text-lg font-bold text-text-primary">{count}</span>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  );
}

export function WorkspaceExecutionsPage() {
  const { id } = useParams();
  const { data: executions, isLoading, isError } = useExecutions(id);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

  const selectedExecution = selectedExecutionId
    ? executions?.find((e) => e.id === selectedExecutionId) ?? null
    : null;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Executions"
        description="Pipeline runs associated with this investigation"
      />

      {isError ? (
        <p className="text-sm text-destructive">
          Failed to load executions.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* List */}
          <div className={selectedExecution ? "lg:col-span-1" : "lg:col-span-3"}>
            <Card>
              <CardHeader>
                <CardTitle>Execution History</CardTitle>
              </CardHeader>
              <CardContent>
                <ExecutionPanel
                  executions={executions}
                  isLoading={isLoading}
                  onSelect={setSelectedExecutionId}
                  selectedId={selectedExecutionId ?? undefined}
                />
              </CardContent>
            </Card>
          </div>

          {/* Monitor */}
          {selectedExecution && (
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-text-primary">
                  Execution Monitor
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedExecutionId(null)}
                >
                  Close
                </Button>
              </div>
              <ExecutionMonitor execution={selectedExecution} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
