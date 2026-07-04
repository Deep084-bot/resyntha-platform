import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { MarkdownViewer } from "../components/MarkdownViewer";

afterEach(cleanup);

describe("MarkdownViewer", () => {
  it("renders paragraph text", () => {
    render(<MarkdownViewer content="Hello world" />);
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("renders heading 1", () => {
    render(<MarkdownViewer content="# Title" />);
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders heading 2", () => {
    render(<MarkdownViewer content="## Section" />);
    expect(screen.getByText("Section")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
  });

  it("renders heading 3", () => {
    render(<MarkdownViewer content="### Subsection" />);
    expect(screen.getByText("Subsection")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3 })).toBeInTheDocument();
  });

  it("renders bold text", () => {
    render(<MarkdownViewer content="Hello **world**" />);
    const strong = screen.getByText("world");
    expect(strong.tagName).toBe("STRONG");
  });

  it("renders italic text", () => {
    render(<MarkdownViewer content="Hello *world*" />);
    const em = screen.getByText("world");
    expect(em.tagName).toBe("EM");
  });

  it("renders inline code", () => {
    render(<MarkdownViewer content="Use `code` here" />);
    expect(screen.getByText("code")).toBeInTheDocument();
  });

  it("renders unordered list", () => {
    render(<MarkdownViewer content={"- Item 1\n- Item 2"} />);
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
  });

  it("renders ordered list", () => {
    render(<MarkdownViewer content={"1. First\n2. Second"} />);
    expect(screen.getByText("First")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
  });

  it("renders code block", () => {
    render(<MarkdownViewer content={"```\nconst x = 1;\n```"} />);
    expect(screen.getByText("const x = 1;")).toBeInTheDocument();
  });

  it("renders blockquote", () => {
    render(<MarkdownViewer content="> A quote" />);
    expect(screen.getByText("A quote")).toBeInTheDocument();
  });

  it("renders horizontal rule", () => {
    const { container } = render(<MarkdownViewer content="---" />);
    expect(container.querySelector("hr")).toBeInTheDocument();
  });

  it("renders link", () => {
    render(<MarkdownViewer content="[Click here](https://example.com)" />);
    const link = screen.getByText("Click here");
    expect(link.tagName).toBe("A");
    expect(link).toHaveAttribute("href", "https://example.com");
  });

  it("renders multiple paragraphs with spacing", () => {
    render(<MarkdownViewer content={"Para one\n\nPara two"} />);
    expect(screen.getByText("Para one")).toBeInTheDocument();
    expect(screen.getByText("Para two")).toBeInTheDocument();
  });
});
