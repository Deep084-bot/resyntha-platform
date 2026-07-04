import { Calendar, RefreshCw, Package, Cpu, Hash } from "lucide-react";

import type { Artifact } from "@/types";
import { formatArtifactType } from "./utils";

export interface ArtifactMetadataProps {
  artifact: Artifact;
}

export function ArtifactMetadata({ artifact }: ArtifactMetadataProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
        Details
      </h3>
      <dl className="space-y-2">
        <MetadataRow
          icon={Package}
          label="Type"
          value={formatArtifactType(artifact.artifact_type)}
        />
        <MetadataRow
          icon={Calendar}
          label="Created"
          value={new Date(artifact.created_at).toLocaleString()}
        />
        <MetadataRow
          icon={RefreshCw}
          label="Updated"
          value={new Date(artifact.updated_at).toLocaleString()}
        />
        <MetadataRow
          icon={Hash}
          label="Version"
          value={`v${artifact.version}`}
        />
        <MetadataRow
          icon={Cpu}
          label="Generator"
          value={artifact.artifact_type
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase())}
        />
      </dl>
    </div>
  );
}

function MetadataRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <Icon className="h-3.5 w-3.5 shrink-0 text-text-muted" />
      <dt className="text-text-muted min-w-16">{label}</dt>
      <dd className="text-text-primary font-medium truncate">{value}</dd>
    </div>
  );
}
