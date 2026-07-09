import api from "@/lib/api";

import type { GraphDTO } from "../types/graph";

export async function fetchGraph(investigationId: string): Promise<GraphDTO> {
  const { data } = await api.get<GraphDTO>(
    `/investigations/${investigationId}/graph`,
  );
  return data;
}
