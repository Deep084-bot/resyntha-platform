import api from "@/lib/api";
import type {
  CreateInvestigationRequest,
  Investigation,
  TimelineEvent,
} from "@/types";

export async function fetchInvestigations(
  skip = 0,
  limit = 100,
): Promise<Investigation[]> {
  const { data } = await api.get<Investigation[]>("/investigations", {
    params: { skip, limit },
  });
  return data;
}

export async function fetchInvestigation(
  id: string,
): Promise<Investigation> {
  const { data } = await api.get<Investigation>(`/investigations/${id}`);
  return data;
}

export async function createInvestigation(
  body: CreateInvestigationRequest,
): Promise<Investigation> {
  const { data } = await api.post<Investigation>("/investigations", body);
  return data;
}

export async function deleteInvestigation(id: string): Promise<void> {
  await api.delete(`/investigations/${id}`);
}

export async function fetchTimeline(
  investigationId: string,
): Promise<TimelineEvent[]> {
  const { data } = await api.get<TimelineEvent[]>(
    `/investigations/${investigationId}/timeline`,
  );
  return data;
}
