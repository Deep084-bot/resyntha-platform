import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Artifact } from "@/types";

import { ArtifactMetadata } from "../components/ArtifactMetadata";

afterEach(cleanup);

const MOCK_ARTIFACT: Artifact = {
  id: "a1",
  investigation_id: "inv1",
  artifact_type: "final_report",
  version: 3,
  status: "ready",
  payload: null,
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

describe("ArtifactMetadata", () => {
  it("renders section heading", () => {
    render(<ArtifactMetadata artifact={MOCK_ARTIFACT} />);
    expect(screen.getByText("Details")).toBeInTheDocument();
  });

  it("renders type", () => {
    render(<ArtifactMetadata artifact={MOCK_ARTIFACT} />);
    const typeEls = screen.getAllByText("Final Report");
    expect(typeEls.length).toBeGreaterThanOrEqual(1);
  });

  it("renders version", () => {
    render(<ArtifactMetadata artifact={MOCK_ARTIFACT} />);
    expect(screen.getByText("v3")).toBeInTheDocument();
  });

  it("renders created timestamp", () => {
    const { container } = render(<ArtifactMetadata artifact={MOCK_ARTIFACT} />);
    // Should render a localized date string
    expect(container.textContent).toContain("2025");
  });

  it("renders all labels", () => {
    render(<ArtifactMetadata artifact={MOCK_ARTIFACT} />);
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("Created")).toBeInTheDocument();
    expect(screen.getByText("Updated")).toBeInTheDocument();
    expect(screen.getByText("Version")).toBeInTheDocument();
    expect(screen.getByText("Generator")).toBeInTheDocument();
  });
});
