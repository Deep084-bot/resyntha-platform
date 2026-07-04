import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LandscapeOverview } from "../components/LandscapeOverview";
import type { LandscapeOverview as OverviewData } from "../types";

afterEach(cleanup);

const mockData: OverviewData = {
  total_papers: 150,
  years_covered: "2020–2024",
  total_institutions: 45,
  total_technologies: 12,
  total_datasets: 28,
  total_methodologies: 9,
  total_authors: 312,
};

describe("LandscapeOverview", () => {
  it("renders years covered", () => {
    render(<LandscapeOverview data={mockData} />);
    expect(screen.getByText(/2020–2024/)).toBeInTheDocument();
  });

  it("renders all metric values", () => {
    render(<LandscapeOverview data={mockData} />);
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(screen.getByText("312")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("28")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
  });

  it("renders all metric labels", () => {
    render(<LandscapeOverview data={mockData} />);
    expect(screen.getByText("Papers")).toBeInTheDocument();
    expect(screen.getByText("Authors")).toBeInTheDocument();
    expect(screen.getByText("Institutions")).toBeInTheDocument();
    expect(screen.getByText("Technologies")).toBeInTheDocument();
    expect(screen.getByText("Datasets")).toBeInTheDocument();
    expect(screen.getByText("Methodologies")).toBeInTheDocument();
  });
});
