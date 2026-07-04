import { useState } from "react";
import { ExternalLink, Bookmark, ChevronDown, ChevronUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Paper } from "@/types";
import { cn } from "@/lib/utils";

export interface PaperCardProps {
  paper: Paper;
  onSelect: (paper: Paper) => void;
  isSelected?: boolean;
  className?: string;
}

function truncateAuthors(authors: string[], max = 3): string {
  if (authors.length === 0) return "Unknown authors";
  const displayed = authors.slice(0, max);
  const suffix = authors.length > max ? ` et al.` : "";
  return displayed.join(", ") + suffix;
}

export function PaperCard({
  paper,
  onSelect,
  isSelected,
  className,
}: PaperCardProps) {
  const [abstractExpanded, setAbstractExpanded] = useState(false);

  const handleClick = () => onSelect(paper);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(paper);
    }
  };

  const hasAbstract = paper.abstract != null && paper.abstract.length > 0;
  const abstractText = paper.abstract ?? "";

  return (
    <article
      className={cn(
        "group relative rounded-lg border bg-surface p-4 transition-all hover:border-border-hover hover:shadow-sm focus-within:ring-2 focus-within:ring-ring",
        isSelected && "border-accent-default ring-1 ring-accent-default",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          {/* Title */}
          <h3
            className="font-medium text-text-primary cursor-pointer hover:text-accent-default transition-colors"
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            role="button"
            tabIndex={0}
            aria-label={`View details for ${paper.title}`}
          >
            {paper.title}
          </h3>

          {/* Authors */}
          <p className="mt-1 text-sm text-text-muted">
            {truncateAuthors(paper.authors)}
          </p>

          {/* Metadata row */}
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-text-muted">
            {paper.year && <span>{paper.year}</span>}
            {paper.venue && (
              <span className="truncate max-w-[200px]">{paper.venue}</span>
            )}
            {paper.citation_count != null && (
              <span>{paper.citation_count} citations</span>
            )}
            <span className="capitalize">{paper.source}</span>
            {paper.doi && (
              <span className="truncate max-w-[180px] font-mono" title={paper.doi}>
                DOI: {paper.doi}
              </span>
            )}
            {paper.score != null && (
              <span>Score: {paper.score.toFixed(2)}</span>
            )}
          </div>

          {/* Abstract preview */}
          {hasAbstract && (
            <div className="mt-2">
              <p
                className={cn(
                  "text-sm text-text-secondary",
                  !abstractExpanded && "line-clamp-3",
                )}
              >
                {abstractText}
              </p>
              {abstractText.length > 200 && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setAbstractExpanded(!abstractExpanded);
                  }}
                  className="mt-1 flex items-center gap-1 text-xs text-accent-default hover:underline"
                  aria-expanded={abstractExpanded}
                  aria-label={abstractExpanded ? "Collapse abstract" : "Expand abstract"}
                >
                  {abstractExpanded ? (
                    <>
                      <ChevronUp className="h-3 w-3" />
                      Show less
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-3 w-3" />
                      Show more
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex shrink-0 flex-col gap-1.5">
          {paper.doi && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              asChild
              aria-label={`Open DOI for ${paper.title} (opens in new tab)`}
            >
              <a
                href={`https://doi.org/${paper.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </Button>
          )}
          {paper.url && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              asChild
              aria-label={`Open PDF for ${paper.title} (opens in new tab)`}
            >
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            aria-label={`Bookmark ${paper.title}`}
            disabled
          >
            <Bookmark className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </article>
  );
}
