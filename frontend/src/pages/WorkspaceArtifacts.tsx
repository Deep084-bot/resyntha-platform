import { useParams } from "react-router-dom";
import { FlaskConical } from "lucide-react";

import { ArtifactCard } from "@/components/ui/artifact-card";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useArtifacts } from "@/hooks/useArtifacts";
import { useInvestigation } from "@/hooks/useInvestigations";
import { useRunInvestigation } from "@/hooks/useExecutions";
import { mapArtifactStatus } from "@/types";

export function WorkspaceArtifactsPage() {
  const { id } = useParams();
  const { data: artifacts, isLoading, isError } = useArtifacts(id);
  const { data: investigation } = useInvestigation(id);
  const runInvestigation = useRunInvestigation(id);

  const handleRunInvestigation = () => {
    const query = investigation?.topic ?? "";
    if (!query) return;
    runInvestigation.mutate({ query, paper_limit: investigation?.paper_limit ?? 10 });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Artifacts"
          description="Durable outputs produced during the investigation"
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Artifacts"
          description="Durable outputs produced during the investigation"
        />
        <p className="text-sm text-destructive">
          Failed to load artifacts.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Artifacts"
        description="Durable outputs produced during the investigation"
      />

      {artifacts && artifacts.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {artifacts.map((a) => (
            <ArtifactCard
              key={a.id}
              title={a.artifact_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              type={a.artifact_type}
              status={mapArtifactStatus(a.status)}
              version={a.version}
              timestamp={`Generated ${new Date(a.created_at).toLocaleDateString()}`}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border">
          <EmptyState
            icon={FlaskConical}
            title="No artifacts yet"
            description="Artifacts will be generated as the pipeline executes"
            action={
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
            }
          />
        </div>
      )}
    </div>
  );
}
