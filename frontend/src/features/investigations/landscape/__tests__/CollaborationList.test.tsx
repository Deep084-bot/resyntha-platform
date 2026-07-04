import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { CollaborationList } from "../components/CollaborationList";
import type { CollaborationData } from "../types";

afterEach(cleanup);

const mockData: CollaborationData = {
  institution_collaborations: [
    { source: "MIT", target: "Stanford", weight: 12 },
    { source: "Google", target: "MIT", weight: 8 },
  ],
  author_collaborations: [
    { source: "Alice Smith", target: "Bob Jones", weight: 5 },
  ],
  centrality_rankings: [
    { name: "MIT", centrality: 0.85, type: "institution" },
    { name: "Alice Smith", centrality: 0.72, type: "author" },
  ],
  total_edges: 3,
};

describe("CollaborationList", () => {
  it("renders institution collaboration section", () => {
    render(<CollaborationList data={mockData} />);
    expect(
      screen.getByText("Institution Collaborations"),
    ).toBeInTheDocument();
  });

  it("renders institution collaboration links", () => {
    render(<CollaborationList data={mockData} />);
    expect(screen.getAllByText("MIT").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Stanford")).toBeInTheDocument();
    expect(screen.getByText("Google")).toBeInTheDocument();
  });

  it("renders author collaboration section", () => {
    render(<CollaborationList data={mockData} />);
    expect(
      screen.getByText("Author Collaborations"),
    ).toBeInTheDocument();
  });

  it("renders author names", () => {
    render(<CollaborationList data={mockData} />);
    expect(screen.getAllByText("Alice Smith").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Bob Jones")).toBeInTheDocument();
  });

  it("renders centrality rankings", () => {
    render(<CollaborationList data={mockData} />);
    expect(
      screen.getByText("Centrality Rankings"),
    ).toBeInTheDocument();
  });

  it("renders centrality values", () => {
    render(<CollaborationList data={mockData} />);
    expect(screen.getByText("0.850")).toBeInTheDocument();
    expect(screen.getByText("0.720")).toBeInTheDocument();
  });

  it("shows total edges", () => {
    render(<CollaborationList data={mockData} />);
    expect(screen.getByText(/Total collaboration edges: 3/)).toBeInTheDocument();
  });

  it("shows empty state when no data", () => {
    const empty: CollaborationData = {
      institution_collaborations: [],
      author_collaborations: [],
      centrality_rankings: [],
      total_edges: 0,
    };
    render(<CollaborationList data={empty} />);
    expect(
      screen.getByText("No collaboration data available."),
    ).toBeInTheDocument();
  });
});
