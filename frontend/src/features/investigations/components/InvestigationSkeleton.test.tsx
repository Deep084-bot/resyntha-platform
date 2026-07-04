import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { InvestigationSkeleton, HeaderSkeleton, TabSkeleton } from "./InvestigationSkeleton";

afterEach(cleanup);

describe("HeaderSkeleton", () => {
  it("renders skeleton placeholders", () => {
    const { container } = render(<HeaderSkeleton />);
    const pulseEls = container.querySelectorAll(".animate-pulse");
    expect(pulseEls.length).toBeGreaterThanOrEqual(3);
  });
});

describe("TabSkeleton", () => {
  it("renders 5 skeleton tab placeholders", () => {
    const { container } = render(<TabSkeleton />);
    const pulseEls = container.querySelectorAll(".animate-pulse");
    expect(pulseEls).toHaveLength(5);
  });
});

describe("InvestigationSkeleton", () => {
  it("renders the full page skeleton", () => {
    const { container } = render(<InvestigationSkeleton />);
    const pulseEls = container.querySelectorAll(".animate-pulse");
    expect(pulseEls.length).toBeGreaterThanOrEqual(8);
  });
});
