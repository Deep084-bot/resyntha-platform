import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { QuickStats } from "./QuickStats";

afterEach(cleanup);

describe("QuickStats", () => {
  it("renders all stat cards", () => {
    render(
      <QuickStats
        stats={{ total: 10, running: 3, completed: 5, failed: 2 }}
      />,
    );

    expect(screen.getByText("Total Investigations")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders zero values", () => {
    render(
      <QuickStats stats={{ total: 0, running: 0, completed: 0, failed: 0 }} />,
    );

    expect(screen.getAllByText("0")).toHaveLength(4);
  });
});
