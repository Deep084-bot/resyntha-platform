import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  FileText,
  RefreshCw,
  Search,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExecutionPanel } from "@/components/ExecutionPanel";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import { useExecution, useExecutionStages, useLatestExecution, useTriggerRetrievalWithPoll } from "@/hooks/useExecutions";
import { useArtifacts } from "@/hooks/useArtifacts";
import { useInvestigation, useTimeline } from "@/hooks/useInvestigations";
import { usePapers } from "@/hooks/useRetrieval";
import { cn } from "@/lib/utils";
import { formatDuration } from "@/lib/format";
import { isExecutionTerminal, mapExecutionStatus, mapTimelineStatus, queryKeys } from "@/types";

function StageMetrics({ executionId }: { executionId: string }) {
  const { data: stages } = useExecutionStages(executionId);

  if (!stages || stages.length === 0) return null;

  const total = stages.length;
  const succeeded = stages.filter((s) => s.status === "completed").length;
  const failed = stages.filter((s) => s.status === "failed").length;
  const retried = stages.filter((s) => s.attempt > 1).length;
  const avgStageDurationMs = stages
    .filter((s) => s.duration_ms != null)
    .reduce((acc, s) => acc + (s.duration_ms ?? 0), 0) / total;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Stage Success Rate"
        value={`${Math.round((succeeded / total) * 100)}%`}
        icon={CheckCircle2}
      />
      <StatCard
        label="Stage Failure Rate"
        value={`${Math.round((failed / total) * 100)}%`}
        icon={AlertCircle}
      />
      <StatCard
        label="Avg Stage Duration"
        value={avgStageDurationMs > 0 ? `${(avgStageDurationMs / 1000).toFixed(1)}s` : "\u2014"}
        icon={Clock}
      />
      <StatCard
        label="Retry Rate"
        value={`${Math.round((retried / total) * 100)}%`}
        icon={RefreshCw}
      />
    </div>
  );
}

function LiveStageProgress({ executionId }: { executionId: string }) {
  const { data: stages } = useExecutionStages(executionId);

  if (!stages || stages.length === 0) {
    return (
      <Card>
        <CardContent className="py-4">
          <p className="text-sm text-text-muted">Waiting for stage data...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {stages.map((s) => (
            <div key={s.id} className="flex items-center gap-3 text-sm">
              <div className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold",
                s.status === "completed" ? "bg-success/10 text-success" :
                s.status === "failed" ? "bg-destructive/10 text-destructive" :
                s.status === "running" ? "bg-accent-default/10 text-accent-default" :
                "bg-surface-active text-text-muted",
              )}>
                {s.status === "completed" ? "\u2713" :
                 s.status === "failed" ? "\u2717" :
                 s.status === "running" ? "\u25CF" :
                 s.attempt > 1 ? "\u21BB" :
                 "\u2014"}
              </div>
              <span className="flex-1 text-text-primary capitalize">{s.stage_name}</span>
              {s.duration_ms != null && (
                <span className="text-text-muted">{(s.duration_ms / 1000).toFixed(1)}s</span>
              )}
              {s.status === "running" && (
                <Spinner size="sm" />
              )}
              {s.error_message && (
                <span className="text-destructive text-xs truncate max-w-[200px]" title={s.error_message}>
                  {s.error_message}
                </span>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function RetrievalMetricsSection({ executionId, investigationId }: { executionId: string; investigationId: string }) {
  const { data: execution } = useExecution(executionId);
  if (!execution) return null;

  const retrievalMetrics = execution.metadata?.retrieval_metrics as Record<string, unknown> | undefined;
  if (!retrievalMetrics) return null;

  const providers = retrievalMetrics.providers as Record<string, Record<string, unknown>> | undefined;
  const papersFetched = retrievalMetrics.papers_fetched as number;
  const papersUnique = retrievalMetrics.papers_unique as number;
  const duplicatesRemoved = retrievalMetrics.duplicates_removed as number;
  const averageScore = retrievalMetrics.average_score as number;
  const cacheEnabled = retrievalMetrics.cache_enabled as boolean;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Retrieval Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3 grid grid-cols-4 gap-3">
          <MetricBox icon={Search} label="Papers Fetched" count={papersFetched ?? 0} color="text-blue-500" />
          <MetricBox icon={CheckCircle2} label="Unique" count={papersUnique ?? 0} color="text-success" />
          <MetricBox icon={AlertCircle} label="Duplicates" count={duplicatesRemoved ?? 0} color="text-warning" />
          <MetricBox icon={Clock} label="Avg Score" count={averageScore ?? 0} color="text-text-muted" />
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
                        <span className="text-destructive" title={m.error as string}>FAIL</span>
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
      </CardContent>
    </Card>
  );
}

function MetricBox({
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

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-text-muted">
          {label}
        </CardTitle>
        <Icon className="h-4 w-4 text-text-muted" />
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
      </CardContent>
    </Card>
  );
}

export function WorkspaceOverviewPage() {
  const { id } = useParams();
  const qc = useQueryClient();
  const [alreadyRunningMessage, setAlreadyRunningMessage] = useState<string | null>(null);
  const prevExecutionStatusRef = useRef<string | null>(null);
  const { data: investigation } = useInvestigation(id);
  const { data: papers } = usePapers(id);
  const { data: artifacts } = useArtifacts(id);
  const { data: timeline } = useTimeline(id);
  const { data: executions, isLoading: execLoading } = useLatestExecution(id);
  const trigger = useTriggerRetrievalWithPoll(id!);

  // Clear "already running" message when the running execution finishes.
  const latestRunning = (executions ?? []).find(
    (e) => !isExecutionTerminal(e.status),
  );
  if (!latestRunning && alreadyRunningMessage) {
    setAlreadyRunningMessage(null);
  }

  // Invalidate downstream queries when the latest execution transitions to
  // a terminal status so that the papers/artifacts/timeline tabs show
  // fresh data without requiring a manual refresh.
  useEffect(() => {
    if (!executions || executions.length === 0) return;
    const latest = executions[0];
    const prev = prevExecutionStatusRef.current;
    prevExecutionStatusRef.current = latest.status;
    if (!prev || prev === latest.status) return;
    if (isExecutionTerminal(latest.status)) {
      qc.invalidateQueries({ queryKey: queryKeys.papers.byInvestigation(id!) });
      qc.invalidateQueries({ queryKey: queryKeys.artifacts.byInvestigation(id!) });
      qc.invalidateQueries({ queryKey: queryKeys.investigations.timeline(id!) });
      qc.invalidateQueries({ queryKey: queryKeys.investigations.detail(id!) });
    }
  }, [executions, qc, id]);

  const completedExecs = (executions ?? []).filter(
    (e) => e.status === "completed",
  );
  const avgDuration =
    completedExecs.length > 0
      ? completedExecs.reduce((acc, e) => {
          const dur =
            e.started_at && e.completed_at
              ? new Date(e.completed_at).getTime() -
                new Date(e.started_at).getTime()
              : 0;
          return acc + dur;
        }, 0) / completedExecs.length
      : null;

  const latestExecution =
    executions && executions.length > 0 ? executions[0] : null;

  const hasExecution = executions && executions.length > 0;
  const isRunning =
    latestExecution &&
    !isExecutionTerminal(latestExecution.status);
  const latestCompleted = latestExecution?.status === "completed";
  const latestFailed = latestExecution?.status === "failed";

  const buttonLabel = (() => {
    if (isRunning) return "Retrieving\u2026";
    if (latestCompleted) return "Run Again";
    if (latestFailed) return "Retry Retrieval";
    return "Start Retrieval";
  })();

  const handleRetrieval = () => {
    const query = investigation?.topic ?? "";
    if (!query) return;
    setAlreadyRunningMessage(null);
    trigger.mutate(
      { query, paper_limit: investigation?.paper_limit ?? 10 },
      {
        onSuccess: (data) => {
          if (data.status === "already_running") {
            setAlreadyRunningMessage(data.message ?? "A retrieval is already running.");
          }
        },
      },
    );
  };

  const retrievalButton = !isRunning ? (
    <Button onClick={handleRetrieval}>
      {buttonLabel}
    </Button>
  ) : (
    <Button disabled>
      <Spinner size="sm" className="mr-2 border-t-white" />
      {buttonLabel}
    </Button>
  );

  const emptyState = !hasExecution && (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <Search className="mb-4 h-12 w-12 text-text-muted" />
        <p className="mb-2 text-lg font-medium text-text-primary">
          This investigation has not been processed yet.
        </p>
        <p className="mb-6 text-sm text-text-muted">
          Press &quot;Start Retrieval&quot; to retrieve research papers
          and begin analysis.
        </p>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-8">
      {/* Header with CTA */}
      <SectionHeader
        title="Overview"
        description={
          investigation
            ? `Topic: ${investigation.topic}`
            : undefined
        }
        action={retrievalButton}
      />

      {alreadyRunningMessage && (
        <div className="rounded-md border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-warning">
          {alreadyRunningMessage}
        </div>
      )}

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Papers Retrieved"
          value={
            papers !== undefined ? papers.length : <Skeleton className="h-7 w-12" />
          }
          icon={Search}
        />
        <StatCard
          label="Artifacts Created"
          value={
            artifacts !== undefined ? artifacts.length : <Skeleton className="h-7 w-12" />
          }
          icon={FileText}
        />
        <StatCard
          label="Executions"
          value={
            executions !== undefined ? executions.length : <Skeleton className="h-7 w-12" />
          }
          icon={Activity}
        />
        <StatCard
          label="Avg. Retrieval Duration"
          value={
            avgDuration !== null
              ? formatDuration(
                  new Date(Date.now() - avgDuration).toISOString(),
                  new Date().toISOString(),
                )
              : "\u2014"
          }
          icon={Clock}
        />
      </div>

      {/* Empty state before first execution */}
      {emptyState}

      {/* Latest execution */}
      {latestExecution && (
        <Card>
          <CardHeader>
            <CardTitle>Latest Execution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3 text-sm">
              <span className="font-mono text-text-primary">
                {latestExecution.id.slice(0, 8)}
              </span>
              <StatusBadge
                status={mapExecutionStatus(latestExecution.status)}
                label={latestExecution.status}
              />
              <span className="text-text-muted">
                {latestExecution.trigger}
              </span>
              {latestExecution.started_at && latestExecution.completed_at && (
                <span className="text-text-muted">
                  {formatDuration(
                    latestExecution.started_at,
                    latestExecution.completed_at,
                  )}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Live stage progress */}
      {latestExecution && isRunning && (
        <LiveStageProgress executionId={latestExecution.id} />
      )}

      {/* Stage Metrics & RetrievalMetrics (latest completed execution) */}
      {latestExecution && latestExecution.status === "completed" && (
        <>
          <StageMetrics executionId={latestExecution.id} />
          <RetrievalMetricsSection executionId={latestExecution.id} investigationId={id!} />
        </>
      )}

      {/* Execution History */}
      {hasExecution && (
        <Card>
          <CardHeader>
            <CardTitle>Execution History</CardTitle>
          </CardHeader>
          <CardContent>
            <ExecutionPanel
              executions={executions?.slice(0, 5)}
              isLoading={execLoading}
            />
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {timeline && timeline.length > 0 ? (
            <div className="space-y-2">
              {timeline.slice(0, 5).map((event, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <StatusBadge
                    status={mapTimelineStatus(event.status)}
                  />
                  <span className="text-text-primary">
                    {event.message}
                  </span>
                  <span className="ml-auto text-xs text-text-muted">
                    {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center rounded-md border border-dashed border-border">
              <p className="text-sm text-text-muted">
                {hasExecution
                  ? "No timeline events recorded yet."
                  : 'Press "Start Retrieval" to begin.'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
