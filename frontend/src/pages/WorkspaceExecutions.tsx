import { useState } from "react";
import { useParams } from "react-router-dom";
import { AlertCircle, CheckCircle2, Clock, Database, SkipForward } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PipelineStageCard } from "@/components/ui/pipeline-stage-card";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import { ExecutionPanel } from "@/components/ExecutionPanel";
import { useExecutionStages, useExecutions, useRunInvestigation } from "@/hooks/useExecutions";
import { useInvestigation } from "@/hooks/useInvestigations";
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

function RetrievalMetrics({ execution }: { execution: Execution }) {
  const retrievalMetrics = execution.metadata?.retrieval_metrics as Record<string, unknown> | undefined;
  if (!retrievalMetrics) return null;

  const providers = retrievalMetrics.providers as Record<string, Record<string, unknown>> | undefined;
  const papersFetched = retrievalMetrics.papers_fetched as number;
  const papersUnique = retrievalMetrics.papers_unique as number;
  const duplicatesRemoved = retrievalMetrics.duplicates_removed as number;
  const averageScore = retrievalMetrics.average_score as number;
  const cacheEnabled = retrievalMetrics.cache_enabled as boolean;

  return (
    <div className="mt-4 border-t border-border pt-4">
      <h4 className="mb-3 text-sm font-medium text-text-primary">Retrieval Metrics</h4>
      <div className="mb-3 grid grid-cols-4 gap-3">
        <StatBox
          icon={Database}
          label="Papers Fetched"
          count={papersFetched ?? 0}
          color="text-blue-500"
        />
        <StatBox
          icon={CheckCircle2}
          label="Unique"
          count={papersUnique ?? 0}
          color="text-success"
        />
        <StatBox
          icon={AlertCircle}
          label="Duplicates"
          count={duplicatesRemoved ?? 0}
          color="text-warning"
        />
        <StatBox
          icon={Clock}
          label="Avg Score"
          count={averageScore ?? 0}
          color="text-text-muted"
        />
      </div>
      {providers && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted">
                <th className="pb-1 pr-3 font-medium">Provider</th>
                <th className="pb-1 pr-3 font-medium">Papers</th>
                <th className="pb-1 pr-3 font-medium">Latency (ms)</th>
                <th className="pb-1 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(providers).map(([name, m]) => (
                <tr key={name} className="border-b border-border/50">
                  <td className="py-1 pr-3 font-mono text-text-primary text-xs">{name}</td>
                  <td className="py-1 pr-3 text-text-primary">{m.papers_returned as number}</td>
                  <td className="py-1 pr-3 text-text-primary">{m.response_time_ms as number}</td>
                  <td className="py-1 text-text-primary">
                    {m.success ? (
                      <span className="text-success">OK</span>
                    ) : (
                      <span className="text-destructive" title={m.error as string}>
                        FAIL
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-2 flex items-center gap-2">
        <span className="text-xs text-text-muted">Cache:</span>
        <span className={`text-xs font-medium ${cacheEnabled ? "text-success" : "text-text-muted"}`}>
          {cacheEnabled ? "Enabled" : "Disabled"}
        </span>
      </div>
    </div>
  );
}

function ExecutionMonitor({ execution }: { execution: Execution }) {
  const { data: stages, isLoading: stagesLoading } = useExecutionStages(execution.id);
  const isTerminal = execution.status === "completed" || execution.status === "failed" || execution.status === "cancelled";
  const isRunning = execution.status === "running";
  const meta = execution.metadata ?? {};

  const workerHost = meta.worker_hostname as string | undefined;
  const workerPid = meta.worker_pid as number | undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span className="font-mono text-sm">{execution.id.slice(0, 8)}</span>
          <StatusBadge
            status={mapExecutionStatus(execution.status)}
            label={execution.status}
          />
          {isRunning && (
            <span className="flex items-center gap-1 text-sm text-accent-default">
              <span className="h-2 w-2 animate-pulse rounded-full bg-accent-default" />
              Running
            </span>
          )}
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
          {workerHost && (
            <div>
              <span className="text-text-muted">Worker: </span>
              <span className="text-text-primary font-mono text-xs">{workerHost}</span>
              {workerPid != null && (
                <span className="text-text-muted ml-1">(PID {workerPid})</span>
              )}
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

        {/* Retrieval metrics */}
        <RetrievalMetrics execution={execution} />
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
  const { data: investigation } = useInvestigation(id);
  const runInvestigation = useRunInvestigation(id);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

  const selectedExecution = selectedExecutionId
    ? executions?.find((e) => e.id === selectedExecutionId) ?? null
    : null;

  const handleRunInvestigation = () => {
    const query = investigation?.topic ?? "";
    if (!query) return;
    runInvestigation.mutate({ query, paper_limit: investigation?.paper_limit ?? 10 });
  };

  const emptyAction = (
    <Button
      onClick={handleRunInvestigation}
      disabled={runInvestigation.isPending}
    >
      {runInvestigation.isPending ? (
        <>
          <Spinner size="sm" className="mr-2 border-t-white" />
          Running…
        </>
      ) : (
        "Run Investigation"
      )}
    </Button>
  );

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
                  emptyAction={emptyAction}
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
