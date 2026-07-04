import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Investigation } from "@/types";

import { InvestigationStatusBadge } from "./InvestigationStatusBadge";

export interface InvestigationCardProps {
  investigation: Investigation;
  onDelete?: () => void;
}

export function InvestigationCard({
  investigation,
  onDelete,
}: InvestigationCardProps) {
  const hasCounts =
    investigation.metadata &&
    (typeof investigation.metadata.paper_count === "number" ||
      typeof investigation.metadata.execution_count === "number");

  return (
    <div
      className={cn(
        "group relative rounded-lg border border-border bg-surface-card",
        "transition-colors hover:border-border-accent hover:bg-surface-hover",
      )}
    >
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <Link
              to={`/investigations/${investigation.id}`}
              className="after:absolute after:inset-0"
            >
              <h3 className="text-sm font-medium text-text-primary truncate">
                {investigation.title}
              </h3>
            </Link>
            <p className="mt-1 text-xs text-text-muted line-clamp-1">
              {investigation.topic}
            </p>
          </div>
          <div className="relative z-10 flex items-center gap-2 shrink-0">
            <InvestigationStatusBadge status={investigation.status} />
            {onDelete && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="rounded-md p-1 text-text-muted opacity-0 transition-opacity hover:text-text-primary group-hover:opacity-100"
                aria-label={`Delete ${investigation.title}`}
              >
                <ArrowUpRight className="h-4 w-4 rotate-45" />
              </button>
            )}
          </div>
        </div>

        <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
          <span>Created {formatDate(investigation.created_at)}</span>
          <span>Updated {formatDate(investigation.updated_at)}</span>
        </div>

        {hasCounts && (
          <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
            {typeof investigation.metadata!.paper_count === "number" && (
              <span>{investigation.metadata!.paper_count} papers</span>
            )}
            {typeof investigation.metadata!.execution_count === "number" && (
              <span>{investigation.metadata!.execution_count} executions</span>
            )}
          </div>
        )}
      </div>

      <Link
        to={`/investigations/${investigation.id}`}
        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-text-muted opacity-0 transition-all hover:text-text-primary group-hover:opacity-100"
        aria-label={`Open ${investigation.title}`}
      >
        <ArrowUpRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
