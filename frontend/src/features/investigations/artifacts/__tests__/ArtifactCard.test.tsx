import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Artifact } from "@/types";

import { ArtifactCard } from "../components/ArtifactCard";
import { formatArtifactType } from "../components/utils";

afterEach(cleanup);

const MOCK_ARTIFACT: Artifact = {
  id: "a1",
  investigation_id: "inv1",
  artifact_type: "final_report",
  version: 2,
  status: "ready",
  payload: { content: "# Report\n\nContent here." },
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

describe("formatArtifactType", () => {
  it("formats snake_case to Title Case", () => {
    expect(formatArtifactType("final_report")).toBe("Final Report");
    expect(formatArtifactType("paper_collection")).toBe("Paper Collection");
    expect(formatArtifactType("execution_plan")).toBe("Execution Plan");
  });
});

describe("ArtifactCard", () => {
  it("renders formatted artifact type", () => {
    render(
      <ArtifactCard artifact={MOCK_ARTIFACT} onSelect={vi.fn()} />,
    );
    expect(screen.getByText("Final Report")).toBeInTheDocument();
  });

  it("renders version", () => {
    render(
      <ArtifactCard artifact={MOCK_ARTIFACT} onSelect={vi.fn()} />,
    );
    expect(screen.getByText("v2")).toBeInTheDocument();
  });

  it("renders created date", () => {
    render(
      <ArtifactCard artifact={MOCK_ARTIFACT} onSelect={vi.fn()} />,
    );
    expect(screen.getByText("1/15/2025")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    render(
      <ArtifactCard artifact={MOCK_ARTIFACT} onSelect={vi.fn()} />,
    );
    expect(screen.getByText("ready")).toBeInTheDocument();
  });

  it("calls onSelect when clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <ArtifactCard artifact={MOCK_ARTIFACT} onSelect={onSelect} />,
    );
    await user.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith("a1");
  });

  it("shows selected state", () => {
    render(
      <ArtifactCard
        artifact={MOCK_ARTIFACT}
        isSelected
        onSelect={vi.fn()}
      />,
    );
    const btn = screen.getByRole("button");
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("has accessible label", () => {
    render(
      <ArtifactCard artifact={MOCK_ARTIFACT} onSelect={vi.fn()} />,
    );
    expect(
      screen.getByLabelText("Final Report artifact"),
    ).toBeInTheDocument();
  });
});
