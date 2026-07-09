import api from "@/lib/api";

import type { ReadingStatus, ReadingStatusSetRequest } from "../types/readingStatus";

export async function getReadingStatus(
  investigationId: string,
  paperId: string,
): Promise<ReadingStatus | null> {
  const { data } = await api.get<ReadingStatus | null>(
    `/investigations/${investigationId}/papers/${paperId}/reading-status`,
  );
  return data;
}

export async function setReadingStatus(
  investigationId: string,
  paperId: string,
  body: ReadingStatusSetRequest,
): Promise<ReadingStatus> {
  const { data } = await api.put<ReadingStatus>(
    `/investigations/${investigationId}/papers/${paperId}/reading-status`,
    body,
  );
  return data;
}
