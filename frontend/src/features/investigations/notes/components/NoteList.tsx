import { FileText, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";

import type { Note } from "../types/notes";

interface NoteListProps {
  notes: Note[];
  selectedNoteId: string | null;
  onSelect: (note: Note) => void;
  onCreate: () => void;
  onDelete: (noteId: string) => void;
  isLoading?: boolean;
}

export function NoteList({
  notes,
  selectedNoteId,
  onSelect,
  onCreate,
  onDelete,
  isLoading,
}: NoteListProps) {
  const [search, setSearch] = useState("");

  const filtered = search.trim()
    ? notes.filter(
        (n) =>
          n.title.toLowerCase().includes(search.toLowerCase()) ||
          n.content.toLowerCase().includes(search.toLowerCase()),
      )
    : notes;

  return (
    <div className="flex h-full flex-col gap-3" role="region" aria-label="Notes list">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search notes..."
            className="w-full rounded-md border border-border bg-card py-1.5 pl-7 pr-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-default"
            aria-label="Search notes"
          />
        </div>
        <button
          type="button"
          onClick={onCreate}
          className="rounded-md bg-accent-default p-1.5 text-white hover:bg-accent-hover transition-colors"
          aria-label="Create note"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto">
        {isLoading && (
          <p className="py-4 text-center text-xs text-text-muted">Loading...</p>
        )}

        {!isLoading && filtered.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-8">
            <FileText className="h-6 w-6 text-text-muted" />
            <p className="text-xs text-text-muted">
              {search ? "No matching notes" : "No notes yet"}
            </p>
          </div>
        )}

        {filtered.map((note) => (
          <div
            key={note.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(note)}
            onKeyDown={(e) => e.key === "Enter" && onSelect(note)}
            className={`group flex cursor-pointer items-start gap-2 rounded-md px-3 py-2 text-left transition-colors ${
              selectedNoteId === note.id
                ? "bg-accent-default/10"
                : "hover:bg-surface-hover"
            }`}
            aria-selected={selectedNoteId === note.id}
          >
            <div className="flex-1 min-w-0">
              <p className="truncate text-xs font-medium text-text-primary">
                {note.title || "Untitled"}
              </p>
              <p className="mt-0.5 line-clamp-2 text-[11px] text-text-muted">
                {note.content || "Empty note"}
              </p>
              <p className="mt-1 text-[10px] text-text-muted">
                {new Date(note.updated_at).toLocaleDateString()}
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(note.id);
              }}
              className="mt-1 hidden rounded p-0.5 text-text-muted hover:text-red-500 group-hover:block transition-colors"
              aria-label={`Delete note: ${note.title}`}
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
