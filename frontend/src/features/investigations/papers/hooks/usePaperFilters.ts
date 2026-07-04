import { useMemo, useState } from "react";

import type { Paper } from "@/types";

export type SortField = "newest" | "oldest" | "most-cited" | "alphabetical";

export interface PaperFiltersState {
  searchQuery: string;
  yearMin: number | null;
  yearMax: number | null;
  sourceProvider: string;
  minCitations: number | null;
  hasPdf: boolean;
  hasDoi: boolean;
  sortBy: SortField;
}

const EMPTY_FILTERS: PaperFiltersState = {
  searchQuery: "",
  yearMin: null,
  yearMax: null,
  sourceProvider: "",
  minCitations: null,
  hasPdf: false,
  hasDoi: false,
  sortBy: "newest",
};

export function usePaperFilters(papers: Paper[] | undefined) {
  const [filters, setFilters] = useState<PaperFiltersState>(EMPTY_FILTERS);

  const setSearchQuery = (searchQuery: string) =>
    setFilters((f) => ({ ...f, searchQuery }));

  const setYearMin = (yearMin: number | null) =>
    setFilters((f) => ({ ...f, yearMin }));

  const setYearMax = (yearMax: number | null) =>
    setFilters((f) => ({ ...f, yearMax }));

  const setSourceProvider = (sourceProvider: string) =>
    setFilters((f) => ({ ...f, sourceProvider }));

  const setMinCitations = (minCitations: number | null) =>
    setFilters((f) => ({ ...f, minCitations }));

  const setHasPdf = (hasPdf: boolean) =>
    setFilters((f) => ({ ...f, hasPdf }));

  const setHasDoi = (hasDoi: boolean) =>
    setFilters((f) => ({ ...f, hasDoi }));

  const setSortBy = (sortBy: SortField) =>
    setFilters((f) => ({ ...f, sortBy }));

  const resetFilters = () => setFilters(EMPTY_FILTERS);

  const filteredPapers = useMemo(() => {
    if (!papers) return [];

    let result = [...papers];

    // Text search across title, authors, abstract, venue
    if (filters.searchQuery) {
      const q = filters.searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.authors.some((a) => a.toLowerCase().includes(q)) ||
          (p.abstract ?? "").toLowerCase().includes(q) ||
          (p.venue ?? "").toLowerCase().includes(q),
      );
    }

    // Year range
    if (filters.yearMin != null) {
      result = result.filter((p) => p.year != null && p.year >= filters.yearMin!);
    }
    if (filters.yearMax != null) {
      result = result.filter((p) => p.year != null && p.year <= filters.yearMax!);
    }

    // Source provider
    if (filters.sourceProvider) {
      result = result.filter(
        (p) => p.source.toLowerCase() === filters.sourceProvider.toLowerCase(),
      );
    }

    // Minimum citations
    if (filters.minCitations != null) {
      result = result.filter(
        (p) => p.citation_count != null && p.citation_count >= filters.minCitations!,
      );
    }

    // Has PDF (non-null url)
    if (filters.hasPdf) {
      result = result.filter((p) => p.url != null);
    }

    // Has DOI
    if (filters.hasDoi) {
      result = result.filter((p) => p.doi != null);
    }

    // Sort
    result.sort((a, b) => {
      switch (filters.sortBy) {
        case "newest":
          return (b.year ?? -Infinity) - (a.year ?? -Infinity);
        case "oldest": {
          const aYear = a.year ?? Infinity;
          const bYear = b.year ?? Infinity;
          return aYear - bYear;
        }
        case "most-cited":
          return (b.citation_count ?? 0) - (a.citation_count ?? 0);
        case "alphabetical":
          return a.title.localeCompare(b.title);
      }
    });

    return result;
  }, [papers, filters]);

  const sourceProviders = useMemo(() => {
    if (!papers) return [];
    return [...new Set(papers.map((p) => p.source))].sort();
  }, [papers]);

  const yearRange = useMemo(() => {
    if (!papers || papers.length === 0) return { min: null, max: null };
    const years = papers
      .map((p) => p.year)
      .filter((y): y is number => y != null);
    if (years.length === 0) return { min: null, max: null };
    return { min: Math.min(...years), max: Math.max(...years) };
  }, [papers]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.searchQuery) count++;
    if (filters.yearMin != null) count++;
    if (filters.yearMax != null) count++;
    if (filters.sourceProvider) count++;
    if (filters.minCitations != null) count++;
    if (filters.hasPdf) count++;
    if (filters.hasDoi) count++;
    return count;
  }, [filters]);

  return {
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
  };
}
