import { FileText, FlaskConical, Layers, BookOpen, Network, FileSearch, Table, TrendingUp, Lightbulb, PenLine, FileCheck } from "lucide-react";

import type { Artifact, ArtifactType } from "@/types";
import { mapArtifactStatus } from "@/types";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";
import { formatArtifactType } from "./utils";

export interface ArtifactCardProps {
  artifact: Artifact;
  isSelected?: boolean;
  onSelect: (id: string) => void;
}

const TYPE_ICONS: Record<ArtifactType, React.ComponentType<{ className?: string }>> = {
  execution_plan: FileCheck,
  paper_collection: Layers,
  validated_collection: BookOpen,
  knowledge_package: Network,
  research_landscape: FlaskConical,
  research_gap_report: FileSearch,
  comparison_matrix: Table,
  trend_report: TrendingUp,
  opportunity_report: Lightbulb,
  research_ideas: PenLine,
  final_report: FileText,
};

export function ArtifactCard({ artifact, isSelected, onSelect }: ArtifactCardProps) {
  const Icon = TYPE_ICONS[artifact.artifact_type] ?? FileText;

  return (
    <button
      type="button"
      onClick={() => onSelect(artifact.id)}
      className={cn(
        "flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left transition-colors",
        isSelected
          ? "border-accent-default/40 bg-accent-default/5"
          : "border-border bg-surface-card hover:bg-surface-active",
      )}
      aria-pressed={isSelected}
      aria-label={`${formatArtifactType(artifact.artifact_type)} artifact`}
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-active">
        <Icon className="h-4 w-4 text-text-secondary" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-text-primary">
            {formatArtifactType(artifact.artifact_type)}
          </span>
          <StatusBadge
            status={mapArtifactStatus(artifact.status)}
            label={artifact.status}
          />
        </div>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-muted">
          <span>v{artifact.version}</span>
          <span>{new Date(artifact.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    </button>
  );
}
