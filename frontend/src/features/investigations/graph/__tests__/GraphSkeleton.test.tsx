import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { GraphSkeleton } from "../components/GraphSkeleton";

afterEach(cleanup);

describe("GraphSkeleton", () => {
  it("renders loading state with aria label", () => {
    render(<GraphSkeleton />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByLabelText("Loading graph")).toBeInTheDocument();
  });
});
