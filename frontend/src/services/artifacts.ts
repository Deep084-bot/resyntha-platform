import api from "@/lib/api";
import type { Artifact } from "@/types";

export async function fetchArtifacts(
  investigationId: string,
): Promise<Artifact[]> {
  const { data } = await api.get<Artifact[]>(
    `/investigations/${investigationId}/artifacts`,
  );
  return data;
}
