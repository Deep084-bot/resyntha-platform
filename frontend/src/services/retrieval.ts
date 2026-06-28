import api from "@/lib/api";
import type { Paper, RetrieveAcceptedResponse, RetrieveRequest } from "@/types";

export async function triggerRetrieval(
  investigationId: string,
  body: RetrieveRequest,
): Promise<RetrieveAcceptedResponse> {
  const { data } = await api.post<RetrieveAcceptedResponse>(
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
