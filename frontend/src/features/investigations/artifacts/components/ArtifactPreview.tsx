import { useEffect, useRef } from "react";
import { FileQuestion } from "lucide-react";

import type { Artifact } from "@/types";

import { MarkdownViewer } from "./MarkdownViewer";
import { JsonViewer } from "./JsonViewer";

export interface ArtifactPreviewProps {
  artifact: Artifact;
}

export function ArtifactPreview({ artifact }: ArtifactPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Focus management when preview changes
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.focus();
    }
  }, [artifact.id]);

  if (!artifact.payload) {
    return (
      <div className="flex h-48 items-center justify-center rounded-md border border-dashed border-border">
        <div className="flex flex-col items-center gap-2 text-text-muted">
          <FileQuestion className="h-8 w-8" />
          <p className="text-sm">No content available</p>
        </div>
      </div>
    );
  }

  const content = artifact.payload.content;

  if (typeof content === "string" && content.trim().length > 0) {
    return (
      <div
        ref={containerRef}
        tabIndex={-1}
        className="rounded-md border border-border bg-surface-card p-4 outline-none"
        role="region"
        aria-label="Artifact markdown preview"
      >
        <MarkdownViewer content={content} />
      </div>
    );
  }

  // Treat any non-null payload object as JSON for display
  return (
    <div
      ref={containerRef}
      tabIndex={-1}
      className="rounded-md border border-border bg-surface-card p-3 outline-none"
      role="region"
      aria-label="Artifact JSON preview"
    >
      <JsonViewer data={artifact.payload} />
    </div>
  );
}
