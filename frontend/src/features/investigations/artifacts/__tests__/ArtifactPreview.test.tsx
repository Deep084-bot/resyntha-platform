import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Artifact } from "@/types";

import { ArtifactPreview } from "../components/ArtifactPreview";

afterEach(cleanup);

const MARKDOWN_ARTIFACT: Artifact = {
  id: "a1",
  investigation_id: "inv1",
  artifact_type: "final_report",
  version: 1,
  status: "ready",
  payload: { content: "# Title\n\nBody text" },
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

const JSON_ARTIFACT: Artifact = {
  id: "a2",
  investigation_id: "inv1",
  artifact_type: "paper_collection",
  version: 1,
  status: "ready",
  payload: { papers: ["p1", "p2"], count: 2 },
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

const NULL_PAYLOAD_ARTIFACT: Artifact = {
  id: "a3",
  investigation_id: "inv1",
  artifact_type: "trend_report",
  version: 1,
  status: "ready",
  payload: null,
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

describe("ArtifactPreview", () => {
  it("renders markdown content", () => {
    render(<ArtifactPreview artifact={MARKDOWN_ARTIFACT} />);
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Body text")).toBeInTheDocument();
  });

  it("renders JSON content", () => {
    const { container } = render(<ArtifactPreview artifact={JSON_ARTIFACT} />);
    expect(container.textContent).toContain("papers");
    expect(container.textContent).toContain("p1");
  });

  it("shows no content message for null payload", () => {
    render(<ArtifactPreview artifact={NULL_PAYLOAD_ARTIFACT} />);
    expect(screen.getByText("No content available")).toBeInTheDocument();
  });

  it("has accessible region label", () => {
    render(<ArtifactPreview artifact={MARKDOWN_ARTIFACT} />);
    expect(
      screen.getByLabelText("Artifact markdown preview"),
    ).toBeInTheDocument();
  });
});
