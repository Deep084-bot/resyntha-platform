import { useCallback, useEffect, useRef, useState } from "react";
import { Save } from "lucide-react";

interface NoteEditorProps {
  noteId: string | null;
  initialTitle: string;
  initialContent: string;
  onSave: (content: string, title: string) => void;
  onClose: () => void;
  onDelete?: () => void;
  isSaving?: boolean;
}

export function NoteEditor({
  noteId,
  initialTitle,
  initialContent,
  onSave,
  onClose,
  onDelete,
  isSaving,
}: NoteEditorProps) {
  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const contentRef = useRef(initialContent);
  const titleRef = useRef(initialTitle);

  useEffect(() => {
    setTitle(initialTitle);
    setContent(initialContent);
    contentRef.current = initialContent;
    titleRef.current = initialTitle;
  }, [initialTitle, initialContent, noteId]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [noteId]);

  const handleContentChange = useCallback(
    (value: string) => {
      setContent(value);
      contentRef.current = value;
    },
    [],
  );

  const handleTitleChange = useCallback(
    (value: string) => {
      setTitle(value);
      titleRef.current = value;
    },
    [],
  );

  const handleSave = useCallback(() => {
    onSave(contentRef.current, titleRef.current);
  }, [onSave]);

  return (
    <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <input
          type="text"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          placeholder="Note title..."
          className="flex-1 bg-transparent text-sm font-medium text-text-primary placeholder:text-text-muted focus:outline-none"
          aria-label="Note title"
        />
        <div className="flex items-center gap-2">
          {isSaving && (
            <span className="flex items-center gap-1 text-[11px] text-text-muted">
              <Save className="h-3 w-3" />
              Saving...
            </span>
          )}
          {noteId && onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="rounded px-2 py-1 text-[11px] text-red-500 hover:bg-red-50 transition-colors"
            >
              Delete
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="rounded px-2 py-1 text-[11px] text-text-muted hover:bg-surface-hover transition-colors"
          >
            Close
          </button>
        </div>
      </div>

      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => handleContentChange(e.target.value)}
        placeholder="Write your notes in markdown..."
        className="min-h-[200px] w-full resize-y rounded border border-border bg-surface-hover/50 p-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-default font-mono leading-relaxed"
        aria-label="Note content"
      />

      <div className="flex items-center justify-between">
        <span className="text-[10px] text-text-muted">
          {content.length} characters
          {noteId ? " · Autosaves on change" : ""}
        </span>
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="rounded-md bg-accent-default px-3 py-1 text-[11px] font-medium text-white hover:bg-accent-hover disabled:opacity-50 transition-colors"
        >
          Save
        </button>
      </div>
    </div>
  );
}
