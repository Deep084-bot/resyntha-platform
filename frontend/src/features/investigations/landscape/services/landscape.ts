import api from "@/lib/api";

import type { LandscapeData } from "../types";

export async function fetchLandscape(
  investigationId: string,
): Promise<LandscapeData> {
  const { data } = await api.get<LandscapeData>(
    `/investigations/${investigationId}/landscape`,
  );
  return data;
}
