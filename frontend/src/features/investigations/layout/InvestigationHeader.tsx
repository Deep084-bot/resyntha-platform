import { Trash2, Pencil, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/layout/PageTitle";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Investigation } from "@/types";

import { InvestigationStatusBadge } from "../components/InvestigationStatusBadge";

export interface InvestigationHeaderProps {
  investigation: Investigation;
  onDelete?: () => void;
  onEdit?: () => void;
  onRerun?: () => void;
  isDeleting?: boolean;
  className?: string;
}

export function InvestigationHeader({
  investigation,
  onDelete,
  onEdit,
  onRerun,
  isDeleting,
  className,
}: InvestigationHeaderProps) {
  return (
    <div className={cn("space-y-4", className)}>
      {/* Title and status row */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <PageTitle>{investigation.title}</PageTitle>
            <InvestigationStatusBadge status={investigation.status} />
          </div>
          <p className="mt-1 text-sm text-text-muted line-clamp-2">
            {investigation.topic}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={onEdit}
              aria-label={`Edit ${investigation.title}`}
            >
              <Pencil className="h-4 w-4" />
              <span className="hidden sm:inline">Edit</span>
            </Button>
          )}
          {onRerun && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRerun}
              aria-label={`Re-run ${investigation.title}`}
            >
              <RefreshCw className="h-4 w-4" />
              <span className="hidden sm:inline">Re-run</span>
            </Button>
          )}
          {onDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              disabled={isDeleting}
              aria-label={`Delete ${investigation.title}`}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
              <span className="hidden sm:inline text-destructive">Delete</span>
            </Button>
          )}
        </div>
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span>Created {formatDate(investigation.created_at)}</span>
        <span>Updated {formatDate(investigation.updated_at)}</span>
        <span>Paper limit: {investigation.paper_limit}</span>
      </div>
    </div>
  );
}
