import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { MethodologyList } from "../components/MethodologyList";
import type { Methodology } from "../types";

afterEach(cleanup);

const mockMethodologies: Methodology[] = [
  { name: "Deep Learning", technique_count: 15, paper_count: 80 },
  { name: "Ensemble Methods", technique_count: 8, paper_count: 35 },
];

describe("MethodologyList", () => {
  it("renders methodology names", () => {
    render(<MethodologyList methodologies={mockMethodologies} />);
    expect(screen.getByText("Deep Learning")).toBeInTheDocument();
    expect(screen.getByText("Ensemble Methods")).toBeInTheDocument();
  });

  it("renders technique and paper counts", () => {
    render(<MethodologyList methodologies={mockMethodologies} />);
    const fifteens = screen.getAllByText("15");
    expect(fifteens.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("80")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("35")).toBeInTheDocument();
  });

  it("shows empty state when no methodologies", () => {
    render(<MethodologyList methodologies={[]} />);
    expect(
      screen.getByText("No methodology data available."),
    ).toBeInTheDocument();
  });
});
