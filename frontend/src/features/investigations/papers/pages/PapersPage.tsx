import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { BookOpen, Search, AlertCircle } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { usePapers } from "@/hooks/useRetrieval";
import { SectionHeader } from "@/components/ui/section-header";

import { usePaperFilters } from "../hooks/usePaperFilters";
import { PaperSearch } from "../components/PaperSearch";
import { PaperFilters } from "../components/PaperFilters";
import { PaperSort } from "../components/PaperSort";
import { PaperCard } from "../components/PaperCard";
import { PaperDetailDrawer } from "../components/PaperDetailDrawer";
import type { Paper } from "@/types";

import { RunningMessage } from "@/features/investigations/components/RunningMessage";
import { useInvestigationRun } from "@/features/investigations/layout/InvestigationRunContext";
import { WorkspaceErrorBoundary } from "@/features/investigations/components/WorkspaceErrorBoundary";

export function PapersPage() {
  const { id } = useParams();
  const { data: papers, isLoading, isError, refetch } = usePapers(id);
  const { running } = useInvestigationRun();
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const paperIdFromUrl = searchParams.get("paperId");

  const {
    filters,
    filteredPapers,
    sourceProviders,
    yearRange,
    activeFilterCount,
    setSearchQuery,
    setYearMin,
    setYearMax,
    setSourceProvider,
    setMinCitations,
    setHasPdf,
    setHasDoi,
    setSortBy,
    resetFilters,
  } = usePaperFilters(papers);

  useEffect(() => {
    if (!papers || !paperIdFromUrl) return;

    const matchedPaper = papers.find((paper) => paper.id === paperIdFromUrl);
    if (matchedPaper) {
      setSelectedPaper(matchedPaper);
    }
  }, [papers, paperIdFromUrl]);

  const handleCloseDrawer = () => {
    setSelectedPaper(null);

    if (!paperIdFromUrl) return;

    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("paperId");
    setSearchParams(nextParams, { replace: true });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <SectionHeader title="Papers" />
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <WorkspaceErrorBoundary>
        <div className="flex h-48 flex-col items-center justify-center gap-3">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-destructive font-medium">
            Failed to load papers.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      </WorkspaceErrorBoundary>
    );
  }

  if (!papers || papers.length === 0) {
    if (running) {
      return (
        <div className="space-y-4">
          <SectionHeader title="Papers" />
          <RunningMessage phase="Retrieving papers" />
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full rounded-lg" />
          ))}
        </div>
      );
    }
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-md border border-dashed border-border">
        <BookOpen className="h-10 w-10 text-text-muted" />
        <div className="text-center">
          <p className="text-sm font-medium text-text-primary">
            No papers have been retrieved yet.
          </p>
          <p className="mt-1 text-xs text-text-muted">
            Run an investigation to retrieve papers.
          </p>
        </div>
      </div>
    );
  }

  const showEmptyResults =
    filteredPapers.length === 0 && activeFilterCount > 0;

  return (
    <div className="flex gap-6">
      {/* Filters sidebar */}
      <aside className="hidden w-56 shrink-0 lg:block">
        <div className="sticky top-4 space-y-4">
          <PaperFilters
            filters={filters}
            sourceProviders={sourceProviders}
            yearRange={yearRange}
            activeFilterCount={activeFilterCount}
            onYearMinChange={setYearMin}
            onYearMaxChange={setYearMax}
            onSourceChange={setSourceProvider}
            onMinCitationsChange={setMinCitations}
            onHasPdfChange={setHasPdf}
            onHasDoiChange={setHasDoi}
            onReset={resetFilters}
          />
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Toolbar */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <PaperSearch
            value={filters.searchQuery}
            onChange={setSearchQuery}
            className="flex-1"
          />
          <div className="flex items-center gap-2">
            <PaperSort value={filters.sortBy} onChange={setSortBy} />
            {/* Mobile filters toggle placeholder */}
          </div>
        </div>

        {/* Results count */}
        <p className="mb-3 text-xs text-text-muted">
          {activeFilterCount > 0
            ? `${filteredPapers.length} of ${papers.length} papers match`
            : `${papers.length} paper${papers.length === 1 ? "" : "s"} retrieved`}
        </p>

        {/* Paper list */}
        {showEmptyResults ? (
          <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border">
            <Search className="h-8 w-8 text-text-muted" />
            <div className="text-center">
              <p className="text-sm font-medium text-text-primary">
                No matching papers
              </p>
              <p className="mt-1 text-xs text-text-muted">
                Try adjusting your filters or search query.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={resetFilters}>
              Clear filters
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredPapers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                onSelect={setSelectedPaper}
                isSelected={selectedPaper?.id === paper.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail drawer */}
      <PaperDetailDrawer
        paper={selectedPaper}
        onClose={handleCloseDrawer}
      />
    </div>
  );
}
