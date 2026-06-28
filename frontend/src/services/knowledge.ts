import api from "@/lib/api";
import type { Artifact } from "@/types";

export async function fetchKnowledgeArtifact(
  investigationId: string,
): Promise<Artifact | null> {
  const { data } = await api.get<Artifact[]>(
    `/investigations/${investigationId}/artifacts`,
  );
  const knowledgeArtifacts = data.filter(
    (a) => a.artifact_type === "knowledge_package",
  );
  if (knowledgeArtifacts.length === 0) return null;
  return knowledgeArtifacts.sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )[0];
}
