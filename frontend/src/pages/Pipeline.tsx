import { PipelineStageCard } from "@/components/ui/pipeline-stage-card";
import { SectionHeader } from "@/components/ui/section-header";

const stages = [
  { name: "retrieve", description: "Search external providers for relevant papers", status: "success" as const, duration: "2.3s" },
  { name: "normalize", description: "Convert provider responses into canonical format", status: "success" as const, duration: "0.1s" },
  { name: "deduplicate", description: "Remove duplicate papers by DOI and title", status: "success" as const, duration: "0.2s" },
  { name: "persist", description: "Store papers in the database", status: "success" as const, duration: "0.5s" },
  { name: "extract", description: "Extract structured information from papers", status: "skipped" as const },
  { name: "analyze", description: "Compare and identify research patterns", status: "pending" as const },
];

export function PipelinePage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <SectionHeader
        title="Pipeline"
        description="Monitor the stages of your research pipeline"
      />

      <div className="space-y-2">
        {stages.map((stage) => (
          <PipelineStageCard
            key={stage.name}
            name={stage.name}
            description={stage.description}
            status={stage.status}
            duration={stage.duration}
          />
        ))}
      </div>
    </div>
  );
}
