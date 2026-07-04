import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ObservationCard } from "../components/ObservationCard";
import type { Observation } from "../types";

afterEach(cleanup);

const mockObservation: Observation = {
  category: "trend",
  label: "Transformer architectures dominate NLP research",
  value:
    "Over 80% of papers in 2024 use transformer-based architectures for NLP tasks.",
};

describe("ObservationCard", () => {
  it("renders category", () => {
    render(<ObservationCard observation={mockObservation} />);
    expect(screen.getByText("trend")).toBeInTheDocument();
  });

  it("renders label", () => {
    render(<ObservationCard observation={mockObservation} />);
    expect(
      screen.getByText("Transformer architectures dominate NLP research"),
    ).toBeInTheDocument();
  });

  it("renders value", () => {
    render(<ObservationCard observation={mockObservation} />);
    expect(
      screen.getByText(
        /Over 80% of papers in 2024 use transformer-based architectures/,
      ),
    ).toBeInTheDocument();
  });
});
