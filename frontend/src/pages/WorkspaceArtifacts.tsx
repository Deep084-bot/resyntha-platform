import { FlaskConical } from "lucide-react";

import { ArtifactCard } from "@/components/ui/artifact-card";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";

const artifacts = [
  { title: "Paper Collection", type: "paper_collection", status: "success" as const, version: 1, timestamp: "Generated 5 min ago" },
  { title: "Execution Plan", type: "execution_plan", status: "success" as const, version: 1, timestamp: "Generated 5 min ago" },
];

export function WorkspaceArtifactsPage() {
  const hasArtifacts = artifacts.length > 0;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Artifacts"
        description="Durable outputs produced during the investigation"
      />

      {hasArtifacts ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {artifacts.map((a) => (
            <ArtifactCard key={a.title} {...a} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border">
          <EmptyState
            icon={FlaskConical}
            title="No artifacts yet"
            description="Artifacts will be generated as the pipeline executes"
          />
        </div>
      )}
    </div>
  );
}
