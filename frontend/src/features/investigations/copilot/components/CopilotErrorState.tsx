import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface CopilotErrorStateProps {
  title?: string;
  description: string;
  onRetry: () => void;
}

export function CopilotErrorState({
  title = "We could not send that message.",
  description,
  onRetry,
}: CopilotErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl border border-destructive/20 bg-destructive/5 px-4 py-3"
    >
      <AlertCircle
        className="mt-0.5 h-5 w-5 shrink-0 text-destructive"
        aria-hidden="true"
      />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-sm font-medium text-text-primary">{title}</p>
        <p className="text-sm text-text-muted">{description}</p>
      </div>
      <Button type="button" variant="outline" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}