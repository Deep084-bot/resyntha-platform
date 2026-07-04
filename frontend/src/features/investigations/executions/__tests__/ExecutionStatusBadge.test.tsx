import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { ExecutionStatus } from "@/types";

import { ExecutionStatusBadge } from "../components/ExecutionStatusBadge";

afterEach(cleanup);

describe("ExecutionStatusBadge", () => {
  it.each([
    ["pending", "Pending"],
    ["running", "Running"],
    ["completed", "Completed"],
    ["failed", "Failed"],
  ] as [ExecutionStatus, string][])(
    "renders %s status with label %s",
    (status, label) => {
      render(<ExecutionStatusBadge status={status} />);
      expect(screen.getByText(label)).toBeInTheDocument();
    },
  );

  it("applies custom className", () => {
    const { container } = render(
      <ExecutionStatusBadge status="completed" className="custom-class" />,
    );
    const badge = container.querySelector(".custom-class");
    expect(badge).toBeInTheDocument();
  });
});
