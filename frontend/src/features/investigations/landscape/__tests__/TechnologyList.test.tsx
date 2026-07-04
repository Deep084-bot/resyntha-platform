import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TechnologyList } from "../components/TechnologyList";
import type { Technology } from "../types";

afterEach(cleanup);

const mockTechnologies: Technology[] = [
  { name: "Transformers", first_appearance_year: 2017, paper_count: 95 },
  { name: "Graph Neural Networks", first_appearance_year: 2018, paper_count: 42 },
  { name: "Diffusion Models", first_appearance_year: null, paper_count: 28 },
];

describe("TechnologyList", () => {
  it("renders technology names", () => {
    render(<TechnologyList technologies={mockTechnologies} />);
    expect(screen.getByText("Transformers")).toBeInTheDocument();
    expect(screen.getByText("Graph Neural Networks")).toBeInTheDocument();
  });

  it("renders first appearance year when available", () => {
    render(<TechnologyList technologies={mockTechnologies} />);
    expect(screen.getByText("2017")).toBeInTheDocument();
    expect(screen.getByText("2018")).toBeInTheDocument();
  });

  it("renders paper counts", () => {
    render(<TechnologyList technologies={mockTechnologies} />);
    expect(screen.getByText("95")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("28")).toBeInTheDocument();
  });

  it("does not render first year when null", () => {
    render(<TechnologyList technologies={mockTechnologies} />);
    const firstYearLabels = screen.getAllByText("first year");
    expect(firstYearLabels).toHaveLength(2);
  });

  it("shows empty state when no technologies", () => {
    render(<TechnologyList technologies={[]} />);
    expect(
      screen.getByText("No technology data available."),
    ).toBeInTheDocument();
  });
});
