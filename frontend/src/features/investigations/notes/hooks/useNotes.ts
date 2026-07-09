import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef } from "react";

import {
  createNote,
  deleteNote,
  fetchNotes,
  searchNotes,
  updateNote,
} from "../services/notes";
import type { Note, NoteCreateRequest, NoteUpdateRequest } from "../types/notes";

export function useNotes(investigationId: string | undefined) {
  return useQuery<Note[]>({
    queryKey: ["investigations", investigationId, "notes"],
    queryFn: () => fetchNotes(investigationId!),
    enabled: !!investigationId,
  });
}

export function useNoteSearch(investigationId: string | undefined, query: string) {
  return useQuery<Note[]>({
    queryKey: ["investigations", investigationId, "notes", "search", query],
    queryFn: () => searchNotes(investigationId!, query),
    enabled: !!investigationId && query.length > 0,
  });
}

export function useCreateNote(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: NoteCreateRequest) => createNote(investigationId!, body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "notes"],
      });
    },
  });
}

export function useUpdateNote(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ noteId, body }: { noteId: string; body: NoteUpdateRequest }) =>
      updateNote(noteId, body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "notes"],
      });
    },
  });
}

export function useDeleteNote(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (noteId: string) => deleteNote(noteId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "notes"],
      });
    },
  });
}

const AUTOSAVE_DEBOUNCE_MS = 1500;

export function useAutosave(investigationId: string | undefined) {
  const updateMutation = useUpdateNote(investigationId);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedRef = useRef<string>("");

  const save = useCallback(
    (noteId: string, content: string, title: string) => {
      if (content === lastSavedRef.current) return;
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        lastSavedRef.current = content;
        updateMutation.mutate({ noteId, body: { content, title } });
      }, AUTOSAVE_DEBOUNCE_MS);
    },
    [updateMutation],
  );

  const flush = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  return { save, flush, isSaving: updateMutation.isPending, error: updateMutation.error };
}

export function useOptimisticUpdate(
  investigationId: string | undefined,
) {
  const qc = useQueryClient();
  const updateMut = useUpdateNote(investigationId);

  const optimisticUpdate = useCallback(
    (noteId: string, body: NoteUpdateRequest) => {
      qc.setQueryData<Note[]>(
        ["investigations", investigationId, "notes"],
        (old) =>
          old?.map((n) =>
            n.id === noteId ? { ...n, ...body } : n,
          ) ?? [],
      );
      return updateMut.mutate({ noteId, body });
    },
    [qc, investigationId, updateMut],
  );

  return { optimisticUpdate, ...updateMut };
}
