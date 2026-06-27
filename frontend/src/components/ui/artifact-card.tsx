import { FileText } from "lucide-react";

import { StatusBadge, type StatusVariant } from "@/components/ui/status-badge";

interface ArtifactCardProps {
  title: string;
  type: string;
  status: StatusVariant;
  version: number;
  timestamp?: string;
}

export function ArtifactCard({
  title,
  type,
  status,
  version,
  timestamp,
}: ArtifactCardProps) {
  return (
    <div className="rounded-lg border border-border bg-surface-card p-4 transition-colors hover:bg-surface-hover">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-active">
          <FileText className="h-4 w-4 text-text-secondary" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-text-primary">
            {title}
          </p>
          <p className="text-xs text-text-muted">
            {type} &middot; v{version}
          </p>
          {timestamp && (
            <p className="mt-1 text-xs text-text-muted">{timestamp}</p>
          )}
        </div>
        <StatusBadge status={status} />
      </div>
    </div>
  );
}
