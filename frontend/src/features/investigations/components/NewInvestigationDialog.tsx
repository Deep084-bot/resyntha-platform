import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

export interface NewInvestigationForm {
  title: string;
  topic: string;
  description: string;
  paperLimit: string;
}

export interface NewInvestigationDialogProps {
  isPending: boolean;
  onSubmit: (form: NewInvestigationForm) => void;
  onClose: () => void;
  error?: string | null;
}

export function NewInvestigationDialog({
  isPending,
  onSubmit,
  onClose,
  error,
}: NewInvestigationDialogProps) {
  const titleRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState<NewInvestigationForm>({
    title: "",
    topic: "",
    description: "",
    paperLimit: "10",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof NewInvestigationForm, string>>>({});

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isPending) onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isPending, onClose]);

  const validate = (): boolean => {
    const next: Partial<Record<keyof NewInvestigationForm, string>> = {};
    if (!form.title.trim()) next.title = "Title is required";
    if (!form.topic.trim()) next.topic = "Research query is required";
    if (form.paperLimit) {
      const n = Number(form.paperLimit);
      if (isNaN(n) || n < 1) next.paperLimit = "Minimum paper limit is 1";
      else if (n > 100) next.paperLimit = "Maximum paper limit is 100";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) onSubmit(form);
  };

  const updateField = (
    field: keyof NewInvestigationForm,
    value: string,
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const inputClass = (field: keyof NewInvestigationForm) =>
    cn(
      "w-full rounded-md border bg-surface-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring",
      errors[field]
        ? "border-destructive"
        : "border-input",
    );

  const paperLimitNum = Number(form.paperLimit);
  const limitError =
    form.paperLimit &&
    (isNaN(paperLimitNum) || paperLimitNum < 1 || paperLimitNum > 100)
      ? "Must be between 1 and 100"
      : undefined;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isPending) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-dialog-title"
    >
      <div className="w-full max-w-lg rounded-lg border border-border bg-surface-card p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2
            id="create-dialog-title"
            className="text-lg font-semibold text-text-primary"
          >
            New Investigation
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

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label
              htmlFor="investigation-title"
              className="mb-1 block text-sm font-medium text-text-primary"
            >
              Title <span className="text-destructive">*</span>
            </label>
            <input
              ref={titleRef}
              id="investigation-title"
              value={form.title}
              onChange={(e) => updateField("title", e.target.value)}
              className={inputClass("title")}
              placeholder="e.g. Attention Mechanisms in Transformers"
              aria-invalid={!!errors.title}
              aria-describedby={errors.title ? "title-error" : undefined}
            />
            {errors.title && (
              <p id="title-error" className="mt-1 text-xs text-destructive" role="alert">
                {errors.title}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="investigation-topic"
              className="mb-1 block text-sm font-medium text-text-primary"
            >
              Research Query <span className="text-destructive">*</span>
            </label>
            <textarea
              id="investigation-topic"
              value={form.topic}
              onChange={(e) => updateField("topic", e.target.value)}
              className={cn(inputClass("topic"), "resize-none")}
              rows={3}
              placeholder="Describe the research topic or question…"
              aria-invalid={!!errors.topic}
              aria-describedby={errors.topic ? "topic-error" : undefined}
            />
            {errors.topic && (
              <p id="topic-error" className="mt-1 text-xs text-destructive" role="alert">
                {errors.topic}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="investigation-description"
              className="mb-1 block text-sm font-medium text-text-primary"
            >
              Description
            </label>
            <input
              id="investigation-description"
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              className={inputClass("description")}
              placeholder="Optional description…"
            />
          </div>

          <div>
            <label
              htmlFor="investigation-paper-limit"
              className="mb-1 block text-sm font-medium text-text-primary"
            >
              Paper Limit
            </label>
            <input
              id="investigation-paper-limit"
              type="number"
              min={1}
              max={100}
              value={form.paperLimit}
              onChange={(e) => updateField("paperLimit", e.target.value)}
              className={inputClass("paperLimit")}
              aria-invalid={!!limitError}
            />
            {limitError && (
              <p className="mt-1 text-xs text-text-muted">{limitError}</p>
            )}
          </div>

          {error && (
            <p className="text-xs text-destructive" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? (
                <>
                  <Spinner size="sm" />
                  Creating…
                </>
              ) : (
                "Create Investigation"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
