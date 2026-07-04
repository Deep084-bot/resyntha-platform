import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SectionCard } from "../components/SectionCard";

afterEach(cleanup);

describe("SectionCard", () => {
  it("renders title", () => {
    render(<SectionCard title="Test Section">Content</SectionCard>);
    expect(screen.getByText("Test Section")).toBeInTheDocument();
  });

  it("renders children", () => {
    render(<SectionCard title="Test">Child Content</SectionCard>);
    expect(screen.getByText("Child Content")).toBeInTheDocument();
  });

  it("renders as a section element", () => {
    const { container } = render(
      <SectionCard title="Test">Content</SectionCard>,
    );
    expect(container.querySelector("section")).toBeInTheDocument();
  });

  it("renders action when provided", () => {
    render(
      <SectionCard title="Test" action={<button>Action</button>}>
        Content
      </SectionCard>,
    );
    expect(screen.getByText("Action")).toBeInTheDocument();
  });
});
