import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TemporalTimeline } from "../components/TemporalTimeline";
import type { TemporalTrend } from "../types";

afterEach(cleanup);

const mockTrends: TemporalTrend[] = [
  {
    year: 2022,
    paper_count: 30,
    methodology_adoptions: 5,
    technology_adoptions: 3,
    dataset_usage_count: 8,
  },
  {
    year: 2023,
    paper_count: 55,
    methodology_adoptions: 8,
    technology_adoptions: 6,
    dataset_usage_count: 12,
  },
  {
    year: 2024,
    paper_count: 80,
    methodology_adoptions: 12,
    technology_adoptions: 9,
    dataset_usage_count: 20,
  },
];

describe("TemporalTimeline", () => {
  it("renders years", () => {
    render(<TemporalTimeline trends={mockTrends} />);
    expect(screen.getByText("2022")).toBeInTheDocument();
    expect(screen.getByText("2023")).toBeInTheDocument();
    expect(screen.getByText("2024")).toBeInTheDocument();
  });

  it("renders paper counts", () => {
    render(<TemporalTimeline trends={mockTrends} />);
    expect(screen.getAllByText(/30 papers/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/55 papers/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/80 papers/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders progress bars with aria labels", () => {
    render(<TemporalTimeline trends={mockTrends} />);
    expect(
      screen.getByLabelText("30 papers in 2022"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("80 papers in 2024"),
    ).toBeInTheDocument();
  });

  it("shows methodology, technology, and dataset counts", () => {
    render(<TemporalTimeline trends={mockTrends} />);
    expect(screen.getByText("12 methodologies")).toBeInTheDocument();
    expect(screen.getByText("9 technologies")).toBeInTheDocument();
    expect(screen.getByText("20 datasets")).toBeInTheDocument();
  });

  it("shows empty state when no trends", () => {
    render(<TemporalTimeline trends={[]} />);
    expect(
      screen.getByText("No temporal data available."),
    ).toBeInTheDocument();
  });
});
