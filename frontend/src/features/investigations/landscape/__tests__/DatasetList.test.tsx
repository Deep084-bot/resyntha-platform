import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DatasetList } from "../components/DatasetList";
import type { Dataset } from "../types";

afterEach(cleanup);

const mockDatasets: Dataset[] = [
  { name: "ImageNet", usage_count: 120, diversity_metric: 0.85 },
  { name: "SQuAD", usage_count: 85, diversity_metric: null },
];

describe("DatasetList", () => {
  it("renders dataset names", () => {
    render(<DatasetList datasets={mockDatasets} />);
    expect(screen.getByText("ImageNet")).toBeInTheDocument();
    expect(screen.getByText("SQuAD")).toBeInTheDocument();
  });

  it("renders usage counts", () => {
    render(<DatasetList datasets={mockDatasets} />);
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("renders diversity metric when available", () => {
    render(<DatasetList datasets={mockDatasets} />);
    expect(screen.getByText("0.85")).toBeInTheDocument();
  });

  it("does not render diversity metric when null", () => {
    render(<DatasetList datasets={mockDatasets} />);
    const diversityLabels = screen.getAllByText("diversity");
    expect(diversityLabels).toHaveLength(1);
  });

  it("shows empty state when no datasets", () => {
    render(<DatasetList datasets={[]} />);
    expect(
      screen.getByText("No dataset data available."),
    ).toBeInTheDocument();
  });
});
