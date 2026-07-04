import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface LandscapeErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function LandscapeErrorState({
  message,
  onRetry,
}: LandscapeErrorStateProps) {
  return (
    <div
      className="flex h-64 flex-col items-center justify-center gap-4 rounded-md border border-dashed border-border"
      role="alert"
    >
      <AlertCircle className="h-10 w-10 text-destructive" />
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary">
          Failed to load landscape
        </p>
        <p className="mt-1 text-xs text-text-muted">
          {message ?? "An error occurred while loading the landscape analysis."}
        </p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
