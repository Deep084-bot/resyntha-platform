import { ArrowUpRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Citation } from "@/types";

export interface CitationChipProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
}

export function CitationChip({ citation, onClick }: CitationChipProps) {
  const label = citation.paper_title || citation.paper_id || "Citation";

  if (!citation.paper_id) {
    return (
      <span className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-border bg-surface-hover px-2.5 py-1 text-xs text-text-muted">
        <span className="truncate">{label}</span>
      </span>
    );
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={cn(
        "h-auto min-h-7 max-w-full whitespace-normal break-words justify-start rounded-full border-border bg-surface px-2.5 py-1 text-xs text-text-secondary hover:text-text-primary",
      )}
      onClick={() => onClick?.(citation)}
      aria-label={`Open citation for ${label}`}
    >
      <span className="min-w-0">{label}</span>
      <ArrowUpRight className="h-3 w-3 shrink-0" aria-hidden="true" />
    </Button>
  );
}