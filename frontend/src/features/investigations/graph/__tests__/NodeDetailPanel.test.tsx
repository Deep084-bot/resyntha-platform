import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NodeDetailPanel } from "../components/NodeDetailPanel";
import type { GraphNodeDTO } from "../types/graph";

afterEach(cleanup);

const paperNode: GraphNodeDTO = {
  id: "paper:abc",
  type: "paper",
  label: "Vision Transformer",
  metadata: {
    year: 2020,
    citation_count: 5000,
    venue: "NeurIPS",
    authors: ["Alexey Dosovitskiy", "Lucas Beyer"],
    institutions: ["Google Research"],
    methodology: ["Attention"],
    datasets: ["ImageNet"],
    technologies: ["PyTorch"],
    research_domains: ["Computer Vision"],
    summary: "Introduced pure transformer to vision tasks.",
  },
};

const authorNode: GraphNodeDTO = {
  id: "author:Alexey",
  type: "author",
  label: "Alexey Dosovitskiy",
  metadata: {
    name: "Alexey Dosovitskiy",
    papers: ["abc", "def"],
    institution: "Google Research",
    first_publication_year: 2015,
  },
};

const datasetNode: GraphNodeDTO = {
  id: "dataset:ImageNet",
  type: "dataset",
  label: "ImageNet",
  metadata: {
    name: "ImageNet",
    related_papers: ["abc", "def"],
  },
};

const technologyNode: GraphNodeDTO = {
  id: "technology:PyTorch",
  type: "technology",
  label: "PyTorch",
  metadata: {
    name: "PyTorch",
    type: "framework",
    related_papers: ["abc"],
  },
};

describe("NodeDetailPanel", () => {
  it("renders paper node details", () => {
    render(<NodeDetailPanel node={paperNode} onClose={() => {}} />);
    expect(screen.getByText("Paper")).toBeInTheDocument();
    expect(screen.getByText("Vision Transformer")).toBeInTheDocument();
    expect(screen.getByText("2020")).toBeInTheDocument();
    expect(screen.getByText("5000")).toBeInTheDocument();
    expect(screen.getByText("NeurIPS")).toBeInTheDocument();
    expect(screen.getByText("Alexey Dosovitskiy")).toBeInTheDocument();
  });

  it("renders author node details", () => {
    render(<NodeDetailPanel node={authorNode} onClose={() => {}} />);
    expect(screen.getByText("Author")).toBeInTheDocument();
    expect(screen.getByText("Alexey Dosovitskiy")).toBeInTheDocument();
    expect(screen.getByText("Google Research")).toBeInTheDocument();
    expect(screen.getByText("2015")).toBeInTheDocument();
  });

  it("renders dataset node details", () => {
    render(<NodeDetailPanel node={datasetNode} onClose={() => {}} />);
    expect(screen.getByText("Dataset")).toBeInTheDocument();
    expect(screen.getByText("ImageNet")).toBeInTheDocument();
  });

  it("renders technology node details", () => {
    render(<NodeDetailPanel node={technologyNode} onClose={() => {}} />);
    expect(screen.getByText("Technology")).toBeInTheDocument();
    expect(screen.getByText("framework")).toBeInTheDocument();
  });

  it("has a close button", () => {
    render(<NodeDetailPanel node={paperNode} onClose={() => {}} />);
    expect(screen.getByLabelText("Close detail panel")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = vi.fn();
    render(<NodeDetailPanel node={paperNode} onClose={onClose} />);
    screen.getByLabelText("Close detail panel").click();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("has dialog role", () => {
    render(<NodeDetailPanel node={paperNode} onClose={() => {}} />);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});
