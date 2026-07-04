import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ExecutionSkeleton } from "../components/ExecutionSkeleton";

afterEach(cleanup);

describe("ExecutionSkeleton", () => {
  it("renders skeleton elements", () => {
    const { container } = render(<ExecutionSkeleton />);
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
