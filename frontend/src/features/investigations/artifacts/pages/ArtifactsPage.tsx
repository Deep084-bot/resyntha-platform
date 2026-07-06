import { useParams } from "react-router-dom";

import { SectionHeader } from "@/components/ui/section-header";

import { useArtifactsPage } from "../hooks/useArtifactsPage";
import { ArtifactList } from "../components/ArtifactList";
import { ArtifactPreview } from "../components/ArtifactPreview";
import { ArtifactMetadata } from "../components/ArtifactMetadata";
import { ArtifactDownload } from "../components/ArtifactDownload";
import { ArtifactSkeleton } from "../components/ArtifactSkeleton";
import { ArtifactErrorState } from "../components/ArtifactErrorState";
import { ArtifactEmptyState } from "../components/ArtifactEmptyState";
import { useInvestigationRun } from "@/features/investigations/layout/InvestigationRunContext";
import { RunningMessage } from "@/features/investigations/components/RunningMessage";

export function ArtifactsPage() {
  const { id } = useParams();
  const {
    artifacts,
    selected,
    isLoading,
    isError,
    handleSelect,
    handleRefresh,
  } = useArtifactsPage(id);
  const { running } = useInvestigationRun();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <SectionHeader title="Artifacts" />
        <ArtifactSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-4">
        <SectionHeader title="Artifacts" />
        <ArtifactErrorState onRetry={handleRefresh} />
      </div>
    );
  }

  if (artifacts.length === 0) {
    if (running) {
      return (
        <div className="space-y-4">
          <SectionHeader title="Artifacts" />
          <RunningMessage phase="Generating artifacts" />
          <ArtifactSkeleton />
        </div>
      );
    }
    return (
      <div className="space-y-4">
        <SectionHeader title="Artifacts" />
        <ArtifactEmptyState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Artifacts"
        description={`${artifacts.length} artifact${artifacts.length === 1 ? "" : "s"} generated`}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Sidebar: Artifact list */}
        <div className="lg:col-span-1">
          <ArtifactList
            artifacts={artifacts}
            selectedId={selected?.id}
            onSelect={handleSelect}
          />
        </div>

        {/* Main: Selected artifact details */}
        <div className="space-y-6 lg:col-span-2">
          {selected && (
            <>
              {/* Preview */}
              <div>
                <h2 className="mb-2 text-sm font-semibold text-text-primary">
                  Preview
                </h2>
                <ArtifactPreview artifact={selected} />
              </div>

              {/* Actions */}
              <ArtifactDownload artifact={selected} />

              {/* Metadata */}
              <ArtifactMetadata artifact={selected} />
            </>
          )}

          {!selected && (
            <div className="flex h-48 items-center justify-center rounded-md border border-dashed border-border">
              <p className="text-sm text-text-muted">
                Select an artifact to preview
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
