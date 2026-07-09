import api from "@/lib/api";

import type { Note, NoteCreateRequest, NoteUpdateRequest } from "../types/notes";

export async function fetchNotes(investigationId: string): Promise<Note[]> {
  const { data } = await api.get<Note[]>(
    `/investigations/${investigationId}/notes`,
  );
  return data;
}

export async function createNote(
  investigationId: string,
  body: NoteCreateRequest,
): Promise<Note> {
  const { data } = await api.post<Note>(
    `/investigations/${investigationId}/notes`,
    body,
  );
  return data;
}

export async function updateNote(
  noteId: string,
  body: NoteUpdateRequest,
): Promise<Note> {
  const { data } = await api.patch<Note>(`/notes/${noteId}`, body);
  return data;
}

export async function deleteNote(noteId: string): Promise<void> {
  await api.delete(`/notes/${noteId}`);
}

export async function searchNotes(
  investigationId: string,
  query: string,
): Promise<Note[]> {
  const { data } = await api.get<Note[]>(
    `/investigations/${investigationId}/notes/search`,
    { params: { q: query } },
  );
  return data;
}

export async function fetchHighlights(
  investigationId: string,
): Promise<Note[]> {
  const { data } = await api.get<Note[]>(
    `/investigations/${investigationId}/notes`,
    { params: { source_type: "copilot" } },
  );
  return data;
}
