import type { ArtifactType } from "@/types";

export function formatArtifactType(type: ArtifactType): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
