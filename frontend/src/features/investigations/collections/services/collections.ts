import api from "@/lib/api";

import type { Collection, CollectionCreateRequest } from "../types/collections";

export async function fetchCollections(investigationId: string): Promise<Collection[]> {
  const { data } = await api.get<Collection[]>(
    `/investigations/${investigationId}/collections`,
  );
  return data;
}

export async function createCollection(
  investigationId: string,
  body: CollectionCreateRequest,
): Promise<Collection> {
  const { data } = await api.post<Collection>(
    `/investigations/${investigationId}/collections`,
    body,
  );
  return data;
}

export async function deleteCollection(collectionId: string): Promise<void> {
  await api.delete(`/collections/${collectionId}`);
}

export async function addPaperToCollection(
  collectionId: string,
  paperId: string,
): Promise<void> {
  await api.post(`/collections/${collectionId}/papers`, {
    paper_id: paperId,
  });
}

export async function removePaperFromCollection(
  collectionId: string,
  paperId: string,
): Promise<void> {
  await api.delete(`/collections/${collectionId}/papers/${paperId}`);
}
