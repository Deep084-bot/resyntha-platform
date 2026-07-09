import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addBookmark,
  fetchBookmarks,
  removeBookmark,
} from "../services/bookmarks";
import type { BookmarkCreateRequest } from "../types/bookmarks";

export function useBookmarks(investigationId: string | undefined) {
  return useQuery({
    queryKey: ["investigations", investigationId, "bookmarks"],
    queryFn: () => fetchBookmarks(investigationId!),
    enabled: !!investigationId,
  });
}

export function useAddBookmark(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: BookmarkCreateRequest) => addBookmark(investigationId!, body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "bookmarks"],
      });
    },
  });
}

export function useRemoveBookmark(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (bookmarkId: string) => removeBookmark(bookmarkId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "bookmarks"],
      });
    },
  });
}
