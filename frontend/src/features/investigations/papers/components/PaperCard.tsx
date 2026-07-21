import { useState } from "react";
import {
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  ChevronDown,
  ChevronUp,
  Circle,
  CheckCircle2,
  BookOpenCheck,
  SkipForward,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Paper, ReadingStatusValue } from "@/types";
import { cn } from "@/lib/utils";

export interface PaperCardProps {
  paper: Paper;
  onSelect: (paper: Paper) => void;
  isSelected?: boolean;
  className?: string;
  isBookmarked?: boolean;
  onToggleBookmark?: () => void;
  readingStatus?: ReadingStatusValue;
  onSetReadingStatus?: (status: ReadingStatusValue) => void;
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
  isBookmarked,
  onToggleBookmark,
  readingStatus,
  onSetReadingStatus,
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
          {/* Bookmark toggle */}
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "h-7 w-7",
              isBookmarked && "text-accent-default",
            )}
            aria-label={isBookmarked ? `Remove bookmark for ${paper.title}` : `Bookmark ${paper.title}`}
            onClick={(e) => {
              e.stopPropagation();
              onToggleBookmark?.();
            }}
          >
            {isBookmarked ? (
              <BookmarkCheck className="h-3.5 w-3.5" />
            ) : (
              <Bookmark className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>

      {/* Reading status */}
      {onSetReadingStatus && (
        <div className="mt-2 flex items-center gap-1.5 border-t border-border pt-2">
          <ReadingStatusBadge status={readingStatus} />
          <select
            value={readingStatus ?? "unread"}
            onChange={(e) => onSetReadingStatus(e.target.value as ReadingStatusValue)}
            onClick={(e) => e.stopPropagation()}
            className="ml-1 rounded border border-border bg-transparent px-2 py-0.5 text-[10px] text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-default"
            aria-label="Reading status"
          >
            <option value="unread">Unread</option>
            <option value="reading">Reading</option>
            <option value="completed">Completed</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>
      )}
    </article>
  );
}

const STATUS_ICONS: Record<string, typeof Circle | undefined> = {
  unread: Circle,
  reading: BookOpenCheck,
  completed: CheckCircle2,
  skipped: SkipForward,
};

const STATUS_COLORS: Record<string, string> = {
  unread: "text-text-muted",
  reading: "text-blue-500",
  completed: "text-emerald-500",
  skipped: "text-orange-500",
};

function ReadingStatusBadge({ status }: { status?: ReadingStatusValue }) {
  const Icon = STATUS_ICONS[status ?? "unread"] ?? Circle;
  const color = STATUS_COLORS[status ?? "unread"];
  return <Icon className={cn("h-3 w-3", color)} />;
}
