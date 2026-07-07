import { Loader2 } from "lucide-react";

export function TypingIndicator() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-2 text-sm text-text-muted"
    >
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span>Copilot is thinking</span>
    </div>
  );
}