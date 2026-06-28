import { useRef } from "react";
import { useParams } from "react-router-dom";
import { BookOpen, ExternalLink, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { usePapers, useTriggerRetrieval } from "@/hooks/useRetrieval";
import type { Paper } from "@/types";

export function WorkspacePapersPage() {
  const { id } = useParams();
  const { data: papers, isLoading, isError } = usePapers(id);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Papers"
        description="Retrieved papers attached to this investigation"
        action={<RetrieveForm investigationId={id!} />}
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-lg" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">
          Failed to load papers.
        </p>
      ) : papers && papers.length > 0 ? (
        <div className="space-y-2">
          {papers.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border">
          <EmptyState
            icon={BookOpen}
            title="No papers collected"
            description="Run the retrieval pipeline to search for papers"
          />
        </div>
      )}
    </div>
  );
}

function PaperCard({ paper }: { paper: Paper }) {
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
            {paper.doi && (
              <span className="font-mono text-[10px]">{paper.doi}</span>
            )}
            {paper.citation_count !== null && paper.citation_count !== undefined && (
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
  const trigger = useTriggerRetrieval(investigationId);

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
          className="rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring w-64"
        />
      </div>
      <div className="w-20">
        <input
          ref={limitRef}
          type="number"
          min={1}
          max={100}
          defaultValue={10}
          className="w-full rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
          title="Paper limit"
        />
      </div>
      <Button type="submit" size="sm" disabled={trigger.isPending}>
        {trigger.isPending ? (
          <Spinner size="sm" className="border-t-white" />
        ) : (
          <Search className="h-4 w-4" />
        )}
        Retrieve
      </Button>
    </form>
  );
}
