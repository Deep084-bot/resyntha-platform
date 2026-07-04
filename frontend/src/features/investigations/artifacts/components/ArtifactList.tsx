import type { Artifact } from "@/types";

import { ArtifactCard } from "./ArtifactCard";

export interface ArtifactListProps {
  artifacts: Artifact[];
  selectedId: string | undefined;
  onSelect: (id: string) => void;
}

export function ArtifactList({
  artifacts,
  selectedId,
  onSelect,
}: ArtifactListProps) {
  return (
    <div className="space-y-2" role="list" aria-label="Artifacts">
      {artifacts.map((artifact) => (
        <div key={artifact.id} role="listitem">
          <ArtifactCard
            artifact={artifact}
            isSelected={selectedId === artifact.id}
            onSelect={onSelect}
          />
        </div>
      ))}
    </div>
  );
}
