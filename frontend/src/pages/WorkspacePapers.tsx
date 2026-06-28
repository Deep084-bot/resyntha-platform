import { useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  BookOpen,
  ExternalLink,
  Search,
  ArrowUpDown,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { useLatestExecution, useTriggerRetrievalWithPoll } from "@/hooks/useExecutions";
import { usePapers } from "@/hooks/useRetrieval";
import type { Paper } from "@/types";

type SortKey = "year" | "citations" | "title";

export function WorkspacePapersPage() {
  const { id } = useParams();
  const { data: papers, isLoading, isError } = usePapers(id);

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
          (p.abstract ?? "").toLowerCase().includes(q),
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
      } else {
        cmp = a.title.localeCompare(b.title);
      }
      return sortDesc ? -cmp : cmp;
    });

    return result;
  }, [papers, search, venueFilter, sortKey, sortDesc]);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Papers"
        description="Retrieved papers attached to this investigation"
        action={<RetrieveForm investigationId={id!} />}
      />

      {/* Filters and sort */}
      {papers && papers.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted" />
            <input
              type="search"
              placeholder="Search papers…"
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
            <Skeleton key={i} className="h-24 w-full rounded-lg" />
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
          />
        </div>
      )}
    </div>
  );
}

function PaperCard({ paper }: { paper: Paper }) {
  const doiUrl = paper.doi
    ? `https://doi.org/${paper.doi}`
    : null;

  return (
    <div className="rounded-lg border border-border bg-surface-card p-4 transition-colors hover:bg-surface-hover">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-active">
          <BookOpen className="h-4 w-4 text-text-secondary" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-sm font-medium text-text-primary">
                {paper.title}
              </p>
              {paper.abstract && (
                <p className="mt-1 text-xs text-text-muted line-clamp-2">
                  {paper.abstract}
                </p>
              )}
            </div>
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 rounded-md p-1 text-text-muted hover:text-text-primary"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-text-muted">
            {paper.venue && <span>{paper.venue}</span>}
            {paper.year && <span>{paper.year}</span>}
            {doiUrl ? (
              <a
                href={doiUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-[10px] text-accent-default hover:underline truncate max-w-[200px]"
              >
                {paper.doi}
              </a>
            ) : null}
            {paper.citation_count !== null &&
              paper.citation_count !== undefined && (
                <span>{paper.citation_count} citations</span>
              )}
          </div>
        </div>
      </div>
    </div>
  );
}

function RetrieveForm({ investigationId }: { investigationId: string }) {
  const queryRef = useRef<HTMLInputElement>(null);
  const limitRef = useRef<HTMLInputElement>(null);
  const trigger = useTriggerRetrievalWithPoll(investigationId);
  const { data: executions } = useLatestExecution(investigationId);

  const isRunning =
    trigger.isPending ||
    (executions &&
      executions.length > 0 &&
      executions[0]?.status === "running");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = queryRef.current?.value.trim();
    if (!query) return;

    trigger.mutate({
      query,
      paper_limit: limitRef.current?.value
        ? Number(limitRef.current.value)
        : undefined,
    });

    if (queryRef.current) queryRef.current.value = "";
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <div>
        <input
          ref={queryRef}
          required
          type="text"
          placeholder="Search query…"
          disabled={isRunning}
          className="rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring w-64 disabled:opacity-50"
        />
      </div>
      <div className="w-20">
        <input
          ref={limitRef}
          type="number"
          min={1}
          max={100}
          defaultValue={10}
          disabled={isRunning}
          className="w-full rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          title="Paper limit"
        />
      </div>
      <Button type="submit" size="sm" disabled={isRunning}>
        {isRunning ? (
          <Spinner size="sm" className="border-t-white" />
        ) : (
          <Search className="h-4 w-4" />
        )}
        Retrieve
      </Button>
    </form>
  );
}
