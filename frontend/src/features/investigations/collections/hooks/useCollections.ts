import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addPaperToCollection,
  createCollection,
  deleteCollection,
  fetchCollections,
  removePaperFromCollection,
} from "../services/collections";
import type { CollectionCreateRequest } from "../types/collections";

export function useCollections(investigationId: string | undefined) {
  return useQuery({
    queryKey: ["investigations", investigationId, "collections"],
    queryFn: () => fetchCollections(investigationId!),
    enabled: !!investigationId,
  });
}

export function useCreateCollection(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CollectionCreateRequest) => createCollection(investigationId!, body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "collections"],
      });
    },
  });
}

export function useDeleteCollection(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (collectionId: string) => deleteCollection(collectionId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "collections"],
      });
    },
  });
}

export function useAddPaperToCollection(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ collectionId, paperId }: { collectionId: string; paperId: string }) =>
      addPaperToCollection(collectionId, paperId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "collections"],
      });
    },
  });
}

export function useRemovePaperFromCollection(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ collectionId, paperId }: { collectionId: string; paperId: string }) =>
      removePaperFromCollection(collectionId, paperId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "collections"],
      });
    },
  });
}
