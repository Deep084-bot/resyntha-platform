import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LandscapeSkeleton } from "../components/LandscapeSkeleton";

afterEach(cleanup);

describe("LandscapeSkeleton", () => {
  it("renders skeleton placeholders", () => {
    const { container } = render(<LandscapeSkeleton />);
    const pulseEls = container.querySelectorAll(".animate-pulse");
    expect(pulseEls.length).toBeGreaterThan(10);
  });
});
