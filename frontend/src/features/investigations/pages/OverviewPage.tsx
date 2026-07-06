import { useParams } from "react-router-dom";
import {
  Activity,
  FileText,
  Clock,
  Search,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useArtifacts } from "@/hooks/useArtifacts";
import { useExecutions } from "@/hooks/useExecutions";
import { useTimeline } from "@/hooks/useInvestigations";
import { usePapers } from "@/hooks/useRetrieval";
import { formatDuration, formatElapsed } from "@/lib/format";
import {
  isExecutionTerminal,
  mapExecutionStatus,
  mapTimelineStatus,
  mapArtifactStatus,
} from "@/types";

import { RunningMessage } from "../components/RunningMessage";
import { useInvestigationRun } from "../layout/InvestigationRunContext";

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

export function OverviewPage() {
  const { id } = useParams();
  const { data: papers, isLoading: papersLoading } = usePapers(id);
  const { data: artifacts, isLoading: artifactsLoading } = useArtifacts(id);
  const { data: executions, isLoading: execLoading } = useExecutions(id);
  const { data: timeline, isLoading: timelineLoading } = useTimeline(id);
  const { running } = useInvestigationRun();

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
  const isRunning =
    latestExecution && !isExecutionTerminal(latestExecution.status);

  const readyArtifacts = (artifacts ?? []).filter((a) => a.status === "ready");
  const recentArtifacts = readyArtifacts.slice(0, 5);

  const hasExecution = executions && executions.length > 0;

  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Papers Retrieved"
          value={
            papersLoading ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              papers?.length ?? 0
            )
          }
          icon={Search}
        />
        <StatCard
          label="Artifacts Created"
          value={
            artifactsLoading ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              artifacts?.length ?? 0
            )
          }
          icon={FileText}
        />
        <StatCard
          label="Executions"
          value={
            execLoading ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              executions?.length ?? 0
            )
          }
          icon={Activity}
        />
        <StatCard
          label="Avg. Execution Duration"
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
              {isRunning && (
                <span className="flex h-2 w-2">
                  <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-accent-default opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-default" />
                </span>
              )}
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

      {/* Recent Artifacts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Artifacts</CardTitle>
        </CardHeader>
        <CardContent>
          {recentArtifacts.length > 0 ? (
            <div className="space-y-2">
              {recentArtifacts.map((artifact) => (
                <div
                  key={artifact.id}
                  className="flex items-center gap-3 text-sm"
                >
                  <StatusBadge
                    status={mapArtifactStatus(artifact.status)}
                    label={artifact.artifact_type}
                  />
                  <span className="text-xs text-text-muted ml-auto">
                    {formatElapsed(artifact.created_at)}
                  </span>
              </div>
            ))}
          </div>
          ) : running ? (
            <RunningMessage phase="Generating artifacts" />
        ) : (
          <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
            <p className="text-sm text-text-muted">
              {hasExecution
                ? "No artifacts generated yet."
                : "No executions have been run yet."}
            </p>
          </div>
        )}
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
            {timeline.slice(-5).reverse().map((event, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <StatusBadge
                  status={mapTimelineStatus(event.status)}
                />
                <span className="text-text-primary">{event.message}</span>
                <span className="ml-auto text-xs text-text-muted">
                  {formatElapsed(event.created_at)}
                </span>
              </div>
            ))}
          </div>
          ) : running ? (
            <RunningMessage phase="Tracking activity" />
        ) : (
          <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
            <p className="text-sm text-text-muted">
              {timelineLoading
                ? "Loading activity..."
                : hasExecution
                  ? "No timeline events recorded yet."
                  : "No executions have been run yet."}
            </p>
          </div>
        )}
        </CardContent>
      </Card>
    </div>
  );
}
