import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ArtifactSkeleton } from "../components/ArtifactSkeleton";

afterEach(cleanup);

describe("ArtifactSkeleton", () => {
  it("renders skeleton elements", () => {
    const { container } = render(<ArtifactSkeleton />);
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
