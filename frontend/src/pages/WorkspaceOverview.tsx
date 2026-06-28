import { useParams } from "react-router-dom";
import { Activity, AlertCircle, CheckCircle2, Clock, FileText, RefreshCw, Search } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExecutionPanel } from "@/components/ExecutionPanel";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useExecutionStages, useExecutions } from "@/hooks/useExecutions";
import { useArtifacts } from "@/hooks/useArtifacts";
import { useTimeline } from "@/hooks/useInvestigations";
import { usePapers } from "@/hooks/useRetrieval";
import { formatDuration } from "@/lib/format";
import { mapExecutionStatus, mapTimelineStatus } from "@/types";

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
  const { data: papers } = usePapers(id);
  const { data: artifacts } = useArtifacts(id);
  const { data: timeline } = useTimeline(id);
  const { data: executions, isLoading: execLoading } = useExecutions(id);

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

  return (
    <div className="space-y-8">
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

      {/* Stage Metrics (latest execution) */}
      {latestExecution && latestExecution.status === "completed" && (
        <StageMetrics executionId={latestExecution.id} />
      )}

      {/* Execution History */}
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
                No activity yet. Run the retrieval pipeline to get started.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
