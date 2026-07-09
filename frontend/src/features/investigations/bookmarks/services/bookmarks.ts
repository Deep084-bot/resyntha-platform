import api from "@/lib/api";

import type { Bookmark, BookmarkCreateRequest } from "../types/bookmarks";

export async function fetchBookmarks(investigationId: string): Promise<Bookmark[]> {
  const { data } = await api.get<Bookmark[]>(
    `/investigations/${investigationId}/bookmarks`,
  );
  return data;
}

export async function addBookmark(
  investigationId: string,
  body: BookmarkCreateRequest,
): Promise<Bookmark> {
  const { data } = await api.post<Bookmark>(
    `/investigations/${investigationId}/bookmarks`,
    body,
  );
  return data;
}

export async function removeBookmark(bookmarkId: string): Promise<void> {
  await api.delete(`/bookmarks/${bookmarkId}`);
}
