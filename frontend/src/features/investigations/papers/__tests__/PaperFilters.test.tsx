import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { SortField } from "../hooks/usePaperFilters";
import type { PaperFiltersState } from "../hooks/usePaperFilters";
import { PaperFilters } from "../components/PaperFilters";

afterEach(cleanup);

const defaultFilters: PaperFiltersState = {
  searchQuery: "",
  yearMin: null,
  yearMax: null,
  sourceProvider: "",
  minCitations: null,
  hasPdf: false,
  hasDoi: false,
  sortBy: "newest" as SortField,
};

function renderFilters(overrides: Partial<typeof defaultFilters> = {}) {
  const filters = { ...defaultFilters, ...overrides };
  return render(
    <PaperFilters
      filters={filters}
      sourceProviders={["arxiv", "pubmed", "crossref"]}
      yearRange={{ min: 2020, max: 2024 }}
      activeFilterCount={0}
      onYearMinChange={vi.fn()}
      onYearMaxChange={vi.fn()}
      onSourceChange={vi.fn()}
      onMinCitationsChange={vi.fn()}
      onHasPdfChange={vi.fn()}
      onHasDoiChange={vi.fn()}
      onReset={vi.fn()}
    />,
  );
}

describe("PaperFilters", () => {
  it("renders filter heading", () => {
    renderFilters();
    expect(screen.getByText("Filters")).toBeInTheDocument();
  });

  it("renders year inputs", () => {
    renderFilters();
    expect(
      screen.getByLabelText("Minimum year"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Maximum year"),
    ).toBeInTheDocument();
  });

  it("renders source provider select", () => {
    renderFilters();
    expect(
      screen.getByLabelText("Filter by source provider"),
    ).toBeInTheDocument();
  });

  it("renders min citations input", () => {
    renderFilters();
    expect(
      screen.getByLabelText("Minimum citation count"),
    ).toBeInTheDocument();
  });

  it("renders Has PDF checkbox", () => {
    renderFilters();
    expect(
      screen.getByLabelText("Only show papers with PDF available"),
    ).toBeInTheDocument();
  });

  it("renders Has DOI checkbox", () => {
    renderFilters();
    expect(
      screen.getByLabelText("Only show papers with DOI"),
    ).toBeInTheDocument();
  });

  it("calls onReset when reset button is clicked and filters are active", async () => {
    const user = userEvent.setup();
    const onReset = vi.fn();
    render(
      <PaperFilters
        filters={defaultFilters}
        sourceProviders={["arxiv"]}
        yearRange={{ min: 2020, max: 2024 }}
        activeFilterCount={3}
        onYearMinChange={vi.fn()}
        onYearMaxChange={vi.fn()}
        onSourceChange={vi.fn()}
        onMinCitationsChange={vi.fn()}
        onHasPdfChange={vi.fn()}
        onHasDoiChange={vi.fn()}
        onReset={onReset}
      />,
    );
    await user.click(screen.getByText("Reset"));
    expect(onReset).toHaveBeenCalledOnce();
  });

  it("shows active filter count badge when filters are active", () => {
    render(
      <PaperFilters
        filters={defaultFilters}
        sourceProviders={["arxiv"]}
        yearRange={{ min: 2020, max: 2024 }}
        activeFilterCount={3}
        onYearMinChange={vi.fn()}
        onYearMaxChange={vi.fn()}
        onSourceChange={vi.fn()}
        onMinCitationsChange={vi.fn()}
        onHasPdfChange={vi.fn()}
        onHasDoiChange={vi.fn()}
        onReset={vi.fn()}
      />,
    );
    expect(screen.getByText("3")).toBeInTheDocument();
  });
});
