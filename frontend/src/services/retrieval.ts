import api from "@/lib/api";
import type { Paper, RetrieveRequest, RetrieveResponse } from "@/types";

export async function triggerRetrieval(
  investigationId: string,
  body: RetrieveRequest,
): Promise<RetrieveResponse> {
  const { data } = await api.post<RetrieveResponse>(
    `/investigations/${investigationId}/retrieve`,
    body,
  );
  return data;
}

export async function fetchPapers(
  investigationId: string,
): Promise<Paper[]> {
  const { data } = await api.get<Paper[]>(
    `/investigations/${investigationId}/papers`,
  );
  return data;
}
