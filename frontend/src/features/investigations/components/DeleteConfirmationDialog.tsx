import { useEffect, useRef } from "react";
import { AlertTriangle, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { Investigation } from "@/types";

export interface DeleteConfirmationDialogProps {
  investigation: Investigation;
  isPending: boolean;
  onConfirm: () => void;
  onClose: () => void;
  error?: string | null;
}

export function DeleteConfirmationDialog({
  investigation,
  isPending,
  onConfirm,
  onClose,
  error,
}: DeleteConfirmationDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isPending) onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isPending, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isPending) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
    >
      <div className="w-full max-w-md rounded-lg border border-border bg-surface-card p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2
            id="delete-dialog-title"
            className="text-lg font-semibold text-text-primary"
          >
            Delete Investigation
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={isPending}
            className="rounded-md p-1 text-text-muted hover:text-text-primary"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-md border border-destructive/20 bg-destructive/5 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
            <div>
              <p className="text-sm font-medium text-text-primary">
                {investigation.title}
              </p>
              <p className="mt-1 text-xs text-text-muted">
                This will permanently delete this investigation and all
                associated data including papers, artifacts, timeline events,
                execution history, and knowledge extraction results. This action
                cannot be undone.
              </p>
            </div>
          </div>

          {error && (
            <p className="text-xs text-destructive" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button
              ref={cancelRef}
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={onConfirm}
              disabled={isPending}
            >
              {isPending ? (
                <>
                  <Spinner size="sm" />
                  Deleting…
                </>
              ) : (
                "Delete"
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
