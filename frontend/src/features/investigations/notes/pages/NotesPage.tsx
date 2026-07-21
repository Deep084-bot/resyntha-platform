import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";

import {
  useAutosave,
  useCreateNote,
  useDeleteNote,
  useNotes,
} from "../hooks/useNotes";
import type { Note } from "../types/notes";
import { NoteEditor, NoteList } from "../components";
import { EmptyState } from "@/components/ui/empty-state";
import { FileText } from "lucide-react";

export function NotesPage() {
  const { id } = useParams();
  const { data: notes, isLoading } = useNotes(id);
  const createNote = useCreateNote(id);
  const deleteNote = useDeleteNote(id);
  const autosave = useAutosave(id);

  const [selectedNote, setSelectedNote] = useState<Note | null>(null);

  const handleSelect = useCallback((note: Note) => {
    setSelectedNote(note);
  }, []);

  const handleCreate = useCallback(() => {
    createNote.mutate(
      { title: "", content: "" },
      {
        onSuccess: (note) => {
          setSelectedNote(note);
        },
      },
    );
  }, [createNote]);

  const handleDelete = useCallback(
    (noteId: string) => {
      if (selectedNote?.id === noteId) {
        setSelectedNote(null);
      }
      deleteNote.mutate(noteId);
    },
    [selectedNote, deleteNote],
  );

  const handleSave = useCallback(
    (content: string, title: string) => {
      if (selectedNote) {
        autosave.save(selectedNote.id, content, title);
      }
    },
    [selectedNote, autosave],
  );

  const handleClose = useCallback(() => {
    setSelectedNote(null);
  }, []);

  if (notes && notes.length === 0 && !isLoading) {
    return (
      <EmptyState
        icon={FileText}
        title="No notes yet"
        description="Create your first research note to capture findings and ideas."
        action={
          <button
            type="button"
            onClick={handleCreate}
            className="rounded-md bg-accent-default px-4 py-2 text-xs font-medium text-white hover:bg-accent-hover transition-colors"
          >
            Create Note
          </button>
        }
      />
    );
  }

  return (
    <div className="flex h-full gap-4">
      <div className="w-72 shrink-0 border-r border-border pr-4">
        <NoteList
          notes={notes ?? []}
          selectedNoteId={selectedNote?.id ?? null}
          onSelect={handleSelect}
          onCreate={handleCreate}
          onDelete={handleDelete}
          isLoading={isLoading}
        />
      </div>

      <div className="flex-1">
        {selectedNote ? (
          <NoteEditor
            key={selectedNote.id}
            noteId={selectedNote.id}
            initialTitle={selectedNote.title}
            initialContent={selectedNote.content}
            onSave={handleSave}
            onClose={handleClose}
            onDelete={() => handleDelete(selectedNote.id)}
            isSaving={autosave.isSaving}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <FileText className="mx-auto h-8 w-8 text-text-muted" />
              <p className="mt-2 text-sm text-text-muted">Select a note or create a new one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
