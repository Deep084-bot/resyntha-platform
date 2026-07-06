import { useEffect, useRef, useState } from "react";
import { matchPath, useLocation } from "react-router-dom";
import { CheckCircle2, X } from "lucide-react";

import { useInvestigation } from "@/hooks/useInvestigations";
import { useExecutions } from "@/hooks/useExecutions";
import { isExecutionTerminal, type Execution } from "@/types";
import { cn } from "@/lib/utils";

const TOAST_DURATION_MS = 4000;

/**
 * Renders nothing until a long-running execution transitions to
 * `completed`. On transition, displays a single fixed-position toast in
 * the top-right with the investigation title and an "open" link, then
 * auto-dismisses. Survives tab navigation but is scoped to the current
 * investigation id.
 *
 * Mounted once at the app root (see app/providers.tsx).
 */
export function SuccessToast() {
  const location = useLocation();
  const match = matchPath("/investigations/:id/*", location.pathname);
  const investigationId = match?.params?.id;
  const { data: investigation } = useInvestigation(investigationId);
  const { data: executions } = useExecutions(investigationId);

  const [message, setMessage] = useState<string | null>(null);

  // Track the latest execution's id + status. When the latest id changes
  // (new run) or status flips to terminal completed, fire the toast.
  const lastSeenRef = useRef<{
    id: string | null;
    status: Execution["status"] | null;
  }>({ id: null, status: null });

  useEffect(() => {
    if (!executions || executions.length === 0) return;
    const latest = executions[0];
    if (!latest) return;

    const prev = lastSeenRef.current;

    // Fire only on the transition of the *current* latest execution to
    // a completed state. We avoid firing on first render (when prev.id is
    // null) and on page-load of an already-completed run.
    const isFreshCompletion =
      latest.id === prev.id &&
      prev.status !== null &&
      !isExecutionTerminal(prev.status) &&
      latest.status === "completed";

    // Also fire when a *new* execution was just started and the user is
    // watching it complete for the first time within this session.
    const isFirstSeenCompletion =
      prev.id !== null &&
      prev.id !== latest.id &&
      latest.status === "completed";

    if (isFreshCompletion || isFirstSeenCompletion) {
      const title = investigation?.title ?? "Investigation";
      setMessage(`${title} finished — refreshing results.`);
    }

    lastSeenRef.current = { id: latest.id, status: latest.status };
  }, [executions, investigation?.title]);

  // Auto-dismiss
  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => setMessage(null), TOAST_DURATION_MS);
    return () => clearTimeout(t);
  }, [message]);

  if (!message) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "fixed right-4 top-4 z-50 flex max-w-sm items-start gap-3 rounded-lg border border-success/30 bg-surface px-4 py-3 shadow-lg",
      )}
    >
      <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
      <p className="flex-1 text-sm text-text-primary">{message}</p>
      <button
        type="button"
        onClick={() => setMessage(null)}
        className="text-text-muted hover:text-text-primary"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
