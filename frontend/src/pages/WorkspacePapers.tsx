import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Search,
  ArrowUpDown,
  FileText,
} from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import { usePapers } from "@/hooks/useRetrieval";
import { useInvestigation } from "@/hooks/useInvestigations";
import { useRunInvestigation } from "@/hooks/useExecutions";
import type { Paper } from "@/types";

const PROVIDER_COLORS: Record<string, string> = {
  semantic_scholar: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  arxiv: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  openalex: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
};

function ProviderBadge({ source }: { source: string }) {
  if (!source) return null;
  const display = source.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const colorClass = PROVIDER_COLORS[source] ?? "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium leading-tight", colorClass)}>
      {display}
    </span>
  );
}

type SortKey = "year" | "citations" | "title" | "score" | "source";

export function WorkspacePapersPage() {
  const { id } = useParams();
  const { data: papers, isLoading, isError } = usePapers(id);
  const { data: investigation } = useInvestigation(id);
  const runInvestigation = useRunInvestigation(id);

  const [search, setSearch] = useState("");
  const [venueFilter, setVenueFilter] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("year");
  const [sortDesc, setSortDesc] = useState(true);

  const venues = useMemo(() => {
    if (!papers) return [];
    const v = new Set<string>();
    for (const p of papers) {
      if (p.venue) v.add(p.venue);
    }
    return Array.from(v).sort();
  }, [papers]);

  const filtered = useMemo(() => {
    if (!papers) return [];
    let result = [...papers];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          (p.abstract ?? "").toLowerCase().includes(q) ||
          p.authors.some((a) => a.toLowerCase().includes(q)),
      );
    }

    if (venueFilter) {
      result = result.filter((p) => p.venue === venueFilter);
    }

    result.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "year") {
        cmp = (a.year ?? 0) - (b.year ?? 0);
      } else if (sortKey === "citations") {
        cmp = (a.citation_count ?? 0) - (b.citation_count ?? 0);
      } else if (sortKey === "score") {
        cmp = a.score - b.score;
      } else if (sortKey === "source") {
        cmp = a.source.localeCompare(b.source);
      } else {
        cmp = a.title.localeCompare(b.title);
      }
      return sortDesc ? -cmp : cmp;
    });

    return result;
  }, [papers, search, venueFilter, sortKey, sortDesc]);

  const handleRunInvestigation = () => {
    const query = investigation?.topic ?? "";
    if (!query) return;
    runInvestigation.mutate({ query, paper_limit: investigation?.paper_limit ?? 10 });
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Papers"
        description="Retrieved papers attached to this investigation"
      />

      {/* Filters and sort */}
      {papers && papers.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-0 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted" />
            <input
              type="search"
              placeholder="Search papers, authors…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border border-input bg-surface-base py-1.5 pl-8 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          {venues.length > 1 && (
            <select
              value={venueFilter}
              onChange={(e) => setVenueFilter(e.target.value)}
              className="rounded-md border border-input bg-surface-base px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All venues</option>
              {venues.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          )}
          <div className="flex items-center gap-1 rounded-md border border-input bg-surface-base px-2 py-1.5">
            <ArrowUpDown className="h-3.5 w-3.5 text-text-muted" />
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              className="bg-transparent text-sm text-text-primary focus:outline-none"
            >
              <option value="year">Year</option>
              <option value="citations">Citations</option>
              <option value="title">Title</option>
              <option value="score">Score</option>
              <option value="source">Source</option>
            </select>
            <button
              type="button"
              onClick={() => setSortDesc(!sortDesc)}
              className="text-xs text-text-muted hover:text-text-primary"
            >
              {sortDesc ? "↓" : "↑"}
            </button>
          </div>
        </div>
      )}

      {/* Paper list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full rounded-lg" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">Failed to load papers.</p>
      ) : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border">
          <EmptyState
            icon={BookOpen}
            title={
              search || venueFilter
                ? "No matching papers"
                : "No papers collected"
            }
            description={
              search || venueFilter
                ? "Try adjusting your search or filters."
                : "Run the retrieval pipeline to search for papers"
            }
            action={
              !search && !venueFilter ? (
                <Button
                  onClick={handleRunInvestigation}
                  disabled={runInvestigation.isPending}
                >
                  {runInvestigation.isPending ? (
                    <>
                      <Spinner size="sm" className="mr-2 border-t-white" />
                      Running…
                    </>
                  ) : (
                    "Run Investigation"
                  )}
                </Button>
              ) : undefined
            }
          />
        </div>
      )}
    </div>
  );
}

function PaperCard({ paper }: { paper: Paper }) {
  const [expanded, setExpanded] = useState(false);

  const doiUrl = paper.doi
    ? `https://doi.org/${paper.doi}`
    : null;

  const authorsStr = paper.authors.length > 0
    ? paper.authors.join(", ")
    : null;

  const abstractTruncated = paper.abstract && paper.abstract.length > 300;

  return (
    <div className="rounded-lg border border-border bg-surface-card p-4 transition-colors hover:bg-surface-hover">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-active">
          <BookOpen className="h-4 w-4 text-text-secondary" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-text-primary leading-snug">
                {paper.title}
              </p>
              {authorsStr && (
                <p className="mt-0.5 text-xs text-text-secondary">
                  {authorsStr}
                </p>
              )}
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {paper.score > 0 && (
                <span className="inline-flex items-center rounded-md border border-border bg-surface-base px-1.5 py-0.5 text-[10px] font-medium text-text-muted">
                  Score: {paper.score.toFixed(1)}
                </span>
              )}
              <ProviderBadge source={paper.source} />
            </div>
          </div>

          {paper.abstract && (
            <div className="mt-2">
              <p className={cn(
                "text-xs text-text-muted leading-relaxed",
                !expanded && abstractTruncated && "line-clamp-3",
              )}>
                {paper.abstract}
              </p>
              {abstractTruncated && (
                <button
                  type="button"
                  onClick={() => setExpanded(!expanded)}
                  className="mt-1 flex items-center gap-1 text-[10px] text-accent-default hover:underline"
                >
                  {expanded ? (
                    <>Show less <ChevronUp className="h-3 w-3" /></>
                  ) : (
                    <>Show more <ChevronDown className="h-3 w-3" /></>
                  )}
                </button>
              )}
            </div>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-text-muted">
            {paper.venue && <span>{paper.venue}</span>}
            {paper.year && <span>{paper.year}</span>}
            {paper.citation_count !== null &&
              paper.citation_count !== undefined && (
                <span>{paper.citation_count} citations</span>
              )}
            {doiUrl && (
              <a
                href={doiUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-accent-default hover:underline"
              >
                <ExternalLink className="h-3 w-3" />
                DOI
              </a>
            )}
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-accent-default hover:underline"
              >
                <FileText className="h-3 w-3" />
                PDF
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


