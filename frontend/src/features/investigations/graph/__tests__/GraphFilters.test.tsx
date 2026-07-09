import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GraphFilters } from "../components/GraphFilters";
import type { NodeType } from "../types/graph";

afterEach(cleanup);

const availableTypes: NodeType[] = ["paper", "author", "institution", "dataset", "technology", "methodology", "research_domain"];

describe("GraphFilters", () => {
  it("renders filter buttons for all node types", () => {
    render(
      <GraphFilters
        filters={{ nodeTypes: new Set(availableTypes), searchQuery: "" }}
        onChange={() => {}}
        availableTypes={availableTypes}
      />,
    );
    expect(screen.getByText("Papers")).toBeInTheDocument();
    expect(screen.getByText("Authors")).toBeInTheDocument();
    expect(screen.getByText("Datasets")).toBeInTheDocument();
  });

  it("renders Show All button when all types selected", () => {
    render(
      <GraphFilters
        filters={{ nodeTypes: new Set(availableTypes), searchQuery: "" }}
        onChange={() => {}}
        availableTypes={availableTypes}
      />,
    );
    expect(screen.getByText("Clear All")).toBeInTheDocument();
  });

  it("renders Clear All button when not all types selected", () => {
    render(
      <GraphFilters
        filters={{ nodeTypes: new Set(["paper"]), searchQuery: "" }}
        onChange={() => {}}
        availableTypes={availableTypes}
      />,
    );
    expect(screen.getByText("Show All")).toBeInTheDocument();
  });

  it("calls onChange when a filter button is clicked", () => {
    const onChange = vi.fn();
    render(
      <GraphFilters
        filters={{ nodeTypes: new Set(availableTypes), searchQuery: "" }}
        onChange={onChange}
        availableTypes={availableTypes}
      />,
    );
    fireEvent.click(screen.getByText("Papers"));
    expect(onChange).toHaveBeenCalledOnce();
  });

  it("has aria-pressed attribute on filter buttons", () => {
    render(
      <GraphFilters
        filters={{ nodeTypes: new Set(["paper"]), searchQuery: "" }}
        onChange={() => {}}
        availableTypes={["paper"]}
      />,
    );
    const button = screen.getByText("Papers").closest("button");
    expect(button).toHaveAttribute("aria-pressed", "true");
  });

  it("has a filter group role", () => {
    render(
      <GraphFilters
        filters={{ nodeTypes: new Set(availableTypes), searchQuery: "" }}
        onChange={() => {}}
        availableTypes={availableTypes}
      />,
    );
    expect(screen.getByRole("group")).toBeInTheDocument();
  });
});
