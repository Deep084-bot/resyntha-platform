import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Artifact } from "@/types";

import { ArtifactDownload } from "../components/ArtifactDownload";

afterEach(cleanup);

const MARKDOWN_ARTIFACT: Artifact = {
  id: "a1",
  investigation_id: "inv1",
  artifact_type: "final_report",
  version: 1,
  status: "ready",
  payload: { content: "Hello **world**" },
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

const JSON_ARTIFACT: Artifact = {
  id: "a2",
  investigation_id: "inv1",
  artifact_type: "paper_collection",
  version: 2,
  status: "ready",
  payload: { papers: [] },
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T12:00:00Z",
};

describe("ArtifactDownload", () => {
  it("renders download button", () => {
    render(<ArtifactDownload artifact={MARKDOWN_ARTIFACT} />);
    expect(
      screen.getByRole("button", { name: /download final report/i }),
    ).toBeInTheDocument();
  });

  it("renders copy button for markdown artifacts", () => {
    render(<ArtifactDownload artifact={MARKDOWN_ARTIFACT} />);
    expect(
      screen.getByRole("button", { name: /copy final report content/i }),
    ).toBeInTheDocument();
  });

  it("does not render copy button for JSON artifacts", () => {
    render(<ArtifactDownload artifact={JSON_ARTIFACT} />);
    expect(
      screen.queryByRole("button", { name: /copy/i }),
    ).not.toBeInTheDocument();
  });

  it("shows copied state after copy click", async () => {
    const user = userEvent.setup();
    // Mock clipboard API
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText },
    });

    render(<ArtifactDownload artifact={MARKDOWN_ARTIFACT} />);
    const copyBtn = screen.getByRole("button", { name: /copy final report content/i });
    await user.click(copyBtn);

    expect(screen.getByText("Copied")).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith("Hello **world**");
  });
});
