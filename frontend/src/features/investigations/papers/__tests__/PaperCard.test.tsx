import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Paper } from "@/types";

import { PaperCard } from "../components/PaperCard";

afterEach(cleanup);

const mockPaper: Paper = {
  id: "p1",
  title: "Deep Learning in NLP",
  abstract: "A comprehensive survey of deep learning methods for natural language processing tasks including translation, summarization, question answering, text generation, sentiment analysis, named entity recognition, and part-of-speech tagging. This survey covers transformer architectures, attention mechanisms, and recent advances in large language models.",
  authors: ["Alice Smith", "Bob Jones", "Carol Williams"],
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

function renderCard(paper = mockPaper, onSelect = vi.fn()) {
  return render(<PaperCard paper={paper} onSelect={onSelect} />);
}

describe("PaperCard", () => {
  it("renders title", () => {
    renderCard();
    expect(screen.getByText("Deep Learning in NLP")).toBeInTheDocument();
  });

  it("renders authors with et al. for >3 authors", () => {
    const manyAuthors: Paper = {
      ...mockPaper,
      authors: ["A", "B", "C", "D", "E"],
    };
    renderCard(manyAuthors);
    expect(screen.getByText(/A, B, C et al\./)).toBeInTheDocument();
  });

  it("renders year", () => {
    renderCard();
    expect(screen.getByText("2024")).toBeInTheDocument();
  });

  it("renders venue", () => {
    renderCard();
    expect(screen.getByText("ACL 2024")).toBeInTheDocument();
  });

  it("renders citation count", () => {
    renderCard();
    expect(screen.getByText("50 citations")).toBeInTheDocument();
  });

  it("renders source provider", () => {
    renderCard();
    expect(screen.getByText("arxiv")).toBeInTheDocument();
  });

  it("renders DOI", () => {
    renderCard();
    expect(screen.getByText(/DOI: 10\.1234\/nlp/)).toBeInTheDocument();
  });

  it("renders abstract preview", () => {
    renderCard();
    expect(
      screen.getByText(/comprehensive survey of deep learning/),
    ).toBeInTheDocument();
  });

  it("shows expand/collapse abstract button for long abstracts", () => {
    renderCard();
    expect(
      screen.getByRole("button", { name: /expand abstract/i }),
    ).toBeInTheDocument();
  });

  it("expands abstract when show more is clicked", async () => {
    const user = userEvent.setup();
    renderCard();
    const expandBtn = screen.getByRole("button", { name: /expand abstract/i });
    await user.click(expandBtn);
    expect(
      screen.getByRole("button", { name: /collapse abstract/i }),
    ).toBeInTheDocument();
  });

  it("renders DOI link", () => {
    renderCard();
    const doiLink = screen.getByLabelText(/open doi/i);
    expect(doiLink).toBeInTheDocument();
    expect(doiLink).toHaveAttribute("href", "https://doi.org/10.1234/nlp");
  });

  it("renders PDF link", () => {
    renderCard();
    const pdfLink = screen.getByLabelText(/open pdf/i);
    expect(pdfLink).toBeInTheDocument();
    expect(pdfLink).toHaveAttribute(
      "href",
      "https://example.com/paper1.pdf",
    );
  });

  it("renders disabled bookmark button", () => {
    renderCard();
    const bookmarkBtn = screen.getByLabelText(/bookmark/i);
    expect(bookmarkBtn).toBeDisabled();
  });

  it("calls onSelect when title is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderCard(mockPaper, onSelect);
    await user.click(screen.getByText("Deep Learning in NLP"));
    expect(onSelect).toHaveBeenCalledWith(mockPaper);
  });

  it("does not render expand button for short abstracts", () => {
    const shortAbstractPaper: Paper = {
      ...mockPaper,
      abstract: "Short abstract.",
    };
    renderCard(shortAbstractPaper);
    expect(
      screen.queryByRole("button", { name: /expand abstract/i }),
    ).not.toBeInTheDocument();
  });

  it("renders score", () => {
    renderCard();
    expect(screen.getByText(/Score: 0.95/)).toBeInTheDocument();
  });

  it("shows selected state styling", () => {
    const { container } = render(
      <PaperCard paper={mockPaper} onSelect={vi.fn()} isSelected />,
    );
    const article = container.querySelector("article");
    expect(article?.className).toContain("ring-accent-default");
  });
});
