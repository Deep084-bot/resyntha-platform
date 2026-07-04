import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Paper } from "@/types";

import { PaperDetailDrawer } from "../components/PaperDetailDrawer";

afterEach(cleanup);

const mockPaper: Paper = {
  id: "p1",
  title: "Deep Learning in NLP",
  abstract:
    "A comprehensive survey of deep learning methods for natural language processing.",
  authors: ["Alice Smith", "Bob Jones"],
  doi: "10.1234/nlp",
  venue: "ACL 2024",
  year: 2024,
  citation_count: 50,
  url: "https://example.com/paper1.pdf",
  source: "arxiv",
  score: 0.95,
  created_at: "2025-01-01",
  updated_at: "2025-01-01",
};

function renderDrawer(
  paper: Paper | null = mockPaper,
  onClose = vi.fn(),
) {
  return render(<PaperDetailDrawer paper={paper} onClose={onClose} />);
}

describe("PaperDetailDrawer", () => {
  it("does not render when paper is null", () => {
    const { container } = renderDrawer(null);
    expect(container.innerHTML).toBe("");
  });

  it("renders paper title", () => {
    renderDrawer();
    expect(screen.getByText("Deep Learning in NLP")).toBeInTheDocument();
  });

  it("renders authors", () => {
    renderDrawer();
    expect(
      screen.getByText("Alice Smith, Bob Jones"),
    ).toBeInTheDocument();
  });

  it("renders venue", () => {
    renderDrawer();
    expect(screen.getByText("ACL 2024")).toBeInTheDocument();
  });

  it("renders year", () => {
    renderDrawer();
    expect(screen.getByText("2024")).toBeInTheDocument();
  });

  it("renders citation count", () => {
    renderDrawer();
    expect(screen.getByText("50")).toBeInTheDocument();
  });

  it("renders source", () => {
    renderDrawer();
    expect(screen.getByText("arxiv")).toBeInTheDocument();
  });

  it("renders DOI", () => {
    renderDrawer();
    expect(screen.getByText(/10\.1234\/nlp/)).toBeInTheDocument();
  });

  it("renders abstract", () => {
    renderDrawer();
    expect(
      screen.getByText(/comprehensive survey of deep learning/),
    ).toBeInTheDocument();
  });

  it("renders close button", () => {
    renderDrawer();
    expect(
      screen.getByRole("button", { name: /close paper details/i }),
    ).toBeInTheDocument();
  });

  it("renders external link buttons", () => {
    renderDrawer();
    expect(screen.getByText("Open DOI")).toBeInTheDocument();
    expect(screen.getByText("Open PDF")).toBeInTheDocument();
    expect(screen.getByText("Copy title")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderDrawer(mockPaper, onClose);
    await user.click(
      screen.getByRole("button", { name: /close paper details/i }),
    );
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls onClose when Escape is pressed", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderDrawer(mockPaper, onClose);
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls onClose when backdrop is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderDrawer(mockPaper, onClose);
    const backdrop = screen.getByLabelText("Paper details: Deep Learning in NLP")
      .parentElement?.previousElementSibling;
    if (backdrop) {
      await user.click(backdrop);
      expect(onClose).toHaveBeenCalledOnce();
    }
  });

  it("has dialog role with modal", () => {
    renderDrawer();
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  it("renders relevance score", () => {
    renderDrawer();
    expect(screen.getByText("0.95")).toBeInTheDocument();
  });

  it("does not render Open PDF section when url is null", () => {
    const noUrlPaper = { ...mockPaper, url: null };
    renderDrawer(noUrlPaper);
    expect(screen.queryByText("Open PDF")).not.toBeInTheDocument();
  });

  it("does not render DOI section when doi is null", () => {
    const noDoiPaper = { ...mockPaper, doi: null };
    renderDrawer(noDoiPaper);
    expect(screen.queryByText("Open DOI")).not.toBeInTheDocument();
  });
});
