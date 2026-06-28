import { useParams } from "react-router-dom";
import { Activity, FileText, Search } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePapers } from "@/hooks/useRetrieval";
import { useArtifacts } from "@/hooks/useArtifacts";
import { useTimeline } from "@/hooks/useInvestigations";
import { useInvestigation } from "@/hooks/useInvestigations";
import { mapTimelineStatus } from "@/types";
import { StatusBadge } from "@/components/ui/status-badge";

export function WorkspaceOverviewPage() {
  const { id } = useParams();
  const { data: investigation } = useInvestigation(id);
  const { data: papers } = usePapers(id);
  const { data: artifacts } = useArtifacts(id);
  const { data: timeline } = useTimeline(id);

  return (
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-text-muted">
              Papers Retrieved
            </CardTitle>
            <Search className="h-4 w-4 text-text-muted" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-text-primary">
              {papers !== undefined ? papers.length : <Skeleton className="h-7 w-12" />}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-text-muted">
              Artifacts Created
            </CardTitle>
            <FileText className="h-4 w-4 text-text-muted" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-text-primary">
              {artifacts !== undefined ? artifacts.length : <Skeleton className="h-7 w-12" />}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-text-muted">
              Paper Limit
            </CardTitle>
            <Activity className="h-4 w-4 text-text-muted" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-text-primary">
              {investigation?.paper_limit ?? <Skeleton className="h-7 w-12" />}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-text-muted">
              Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            {investigation ? (
              <StatusBadge
                status={
                  investigation.status === "completed"
                    ? "success"
                    : investigation.status === "failed"
                      ? "failure"
                      : investigation.status === "cancelled"
                        ? "skipped"
                        : "running"
                }
                label={investigation.status}
              />
            ) : (
              <Skeleton className="h-6 w-20 rounded-full" />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent timeline preview */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {timeline && timeline.length > 0 ? (
            <div className="space-y-2">
              {timeline.slice(0, 5).map((event, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 text-sm"
                >
                  <StatusBadge
                    status={mapTimelineStatus(event.status)}
                  />
                  <span className="text-text-primary">{event.message}</span>
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

      {/* Pipeline status */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
            <p className="text-sm text-text-muted">
              Pipeline execution details will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
