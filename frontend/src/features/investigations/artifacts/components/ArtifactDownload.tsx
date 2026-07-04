import { Download, Check } from "lucide-react";
import { useState, useCallback } from "react";

import type { Artifact } from "@/types";

import { formatArtifactType } from "./utils";

export interface ArtifactDownloadProps {
  artifact: Artifact;
}

function getMimeType(artifact: Artifact): string {
  const content = artifact.payload?.content;
  if (typeof content === "string") return "text/markdown";
  return "application/json";
}

function getExtension(artifact: Artifact): string {
  const content = artifact.payload?.content;
  if (typeof content === "string") return "md";
  return "json";
}

function serializePayload(artifact: Artifact): string {
  const content = artifact.payload?.content;
  if (typeof content === "string") return content;
  return JSON.stringify(artifact.payload, null, 2);
}

export function ArtifactDownload({ artifact }: ArtifactDownloadProps) {
  const [copied, setCopied] = useState(false);

  const handleDownload = useCallback(() => {
    const data = serializePayload(artifact);
    const mime = getMimeType(artifact);
    const ext = getExtension(artifact);
    const name = `${formatArtifactType(artifact.artifact_type).replace(/\s+/g, "_").toLowerCase()}_v${artifact.version}.${ext}`;

    const blob = new Blob([data], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [artifact]);

  const handleCopy = useCallback(async () => {
    const data = serializePayload(artifact);
    try {
      await navigator.clipboard.writeText(data);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API may not be available
    }
  }, [artifact]);

  const isMarkdown = typeof artifact.payload?.content === "string";

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={handleDownload}
        className="flex items-center gap-1.5 rounded-md bg-accent-default px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-default/90 transition-colors"
        aria-label={`Download ${formatArtifactType(artifact.artifact_type)}`}
      >
        <Download className="h-3.5 w-3.5" />
        Download
      </button>
      {isMarkdown && (
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md border border-border bg-surface-card px-3 py-1.5 text-xs font-medium text-text-primary hover:bg-surface-active transition-colors"
          aria-label={`Copy ${formatArtifactType(artifact.artifact_type)} content`}
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-success" />
              Copied
            </>
          ) : (
            "Copy content"
          )}
        </button>
      )}
    </div>
  );
}
