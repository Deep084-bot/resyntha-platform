import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Paper } from "@/types";

import { usePaperFilters } from "../hooks/usePaperFilters";

const papers: Paper[] = [
  {
    id: "p1",
    title: "Deep Learning in NLP",
    abstract: "A comprehensive survey of deep learning methods",
    authors: ["Alice Smith", "Bob Jones"],
    doi: "10.1234/nlp",
    venue: "ACL",
    year: 2024,
    citation_count: 50,
    url: "https://example.com/paper1.pdf",
    source: "arxiv",
    score: 0.95,
    created_at: "2025-01-01",
    updated_at: "2025-01-01",
  },
  {
    id: "p2",
    title: "Computer Vision Advances",
    abstract: "Recent advances in computer vision",
    authors: ["Charlie Brown"],
    doi: null,
    venue: "CVPR",
    year: 2023,
    citation_count: 100,
    url: null,
    source: "pubmed",
    score: 0.87,
    created_at: "2025-01-02",
    updated_at: "2025-01-02",
  },
  {
    id: "p3",
    title: "Reinforcement Learning",
    abstract: "Introduction to RL algorithms",
    authors: ["Diana Prince", "Alice Smith"],
    doi: "10.5678/rl",
    venue: "NeurIPS",
    year: 2022,
    citation_count: 30,
    url: "https://example.com/rl.pdf",
    source: "arxiv",
    score: 0.72,
    created_at: "2025-01-03",
    updated_at: "2025-01-03",
  },
  {
    id: "p4",
    title: "Quantum Computing",
    abstract: "Quantum computing for machine learning",
    authors: ["Eve Adams"],
    doi: null,
    venue: "Nature",
    year: null,
    citation_count: null,
    url: null,
    source: "crossref",
    score: 0.6,
    created_at: "2025-01-04",
    updated_at: "2025-01-04",
  },
];

describe("usePaperFilters", () => {
  it("returns all papers when no filters are set", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    expect(result.current.filteredPapers).toHaveLength(4);
  });

  it("filters by search query across title", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSearchQuery("Deep Learning"));
    const filtered = result.current.filteredPapers;
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.id).toBe("p1");
  });

  it("filters by search query across authors", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSearchQuery("Charlie"));
    const filtered = result.current.filteredPapers;
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.id).toBe("p2");
  });

  it("filters by search query across abstract", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSearchQuery("quantum computing"));
    const filtered = result.current.filteredPapers;
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.id).toBe("p4");
  });

  it("filters by search query across venue", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSearchQuery("CVPR"));
    const filtered = result.current.filteredPapers;
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.id).toBe("p2");
  });

  it("filters by year range", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setYearMin(2023));
    expect(result.current.filteredPapers).toHaveLength(2);
    act(() => result.current.setYearMax(2023));
    expect(result.current.filteredPapers).toHaveLength(1);
  });

  it("filters by source provider", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSourceProvider("arxiv"));
    expect(result.current.filteredPapers).toHaveLength(2);
    expect(
      result.current.filteredPapers.every((p) => p.source === "arxiv"),
    ).toBe(true);
  });

  it("filters by minimum citations", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setMinCitations(40));
    expect(result.current.filteredPapers).toHaveLength(2);
    expect(
      result.current.filteredPapers.every(
        (p) => p.citation_count != null && p.citation_count >= 40,
      ),
    ).toBe(true);
  });

  it("filters by hasPdf", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setHasPdf(true));
    expect(result.current.filteredPapers).toHaveLength(2);
    expect(
      result.current.filteredPapers.every((p) => p.url != null),
    ).toBe(true);
  });

  it("filters by hasDoi", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setHasDoi(true));
    expect(result.current.filteredPapers).toHaveLength(2);
    expect(
      result.current.filteredPapers.every((p) => p.doi != null),
    ).toBe(true);
  });

  it("sorts by newest", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSortBy("newest"));
    const ids = result.current.filteredPapers.map((p) => p.id);
    expect(ids).toEqual(["p1", "p2", "p3", "p4"]);
  });

  it("sorts by oldest", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSortBy("oldest"));
    const ids = result.current.filteredPapers.map((p) => p.id);
    expect(ids).toEqual(["p3", "p2", "p1", "p4"]);
  });

  it("sorts by most-cited", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSortBy("most-cited"));
    const ids = result.current.filteredPapers.map((p) => p.id);
    expect(ids).toEqual(["p2", "p1", "p3", "p4"]);
  });

  it("sorts alphabetically", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => result.current.setSortBy("alphabetical"));
    const ids = result.current.filteredPapers.map((p) => p.id);
    expect(ids).toEqual(["p2", "p1", "p4", "p3"]);
  });

  it("resets filters", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    act(() => {
      result.current.setSearchQuery("Deep Learning");
      result.current.setHasDoi(true);
      result.current.setSortBy("oldest");
    });
    expect(result.current.activeFilterCount).toBe(2);
    act(() => result.current.resetFilters());
    expect(result.current.filteredPapers).toHaveLength(4);
    expect(result.current.activeFilterCount).toBe(0);
    expect(result.current.filters.sortBy).toBe("newest");
  });

  it("computes sourceProviders from paper data", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    expect(result.current.sourceProviders).toEqual([
      "arxiv",
      "crossref",
      "pubmed",
    ]);
  });

  it("computes yearRange from paper data", () => {
    const { result } = renderHook(() => usePaperFilters(papers));
    expect(result.current.yearRange).toEqual({ min: 2022, max: 2024 });
  });

  it("returns empty array for undefined papers", () => {
    const { result } = renderHook(() => usePaperFilters(undefined));
    expect(result.current.filteredPapers).toEqual([]);
    expect(result.current.sourceProviders).toEqual([]);
    expect(result.current.yearRange).toEqual({ min: null, max: null });
  });
});
