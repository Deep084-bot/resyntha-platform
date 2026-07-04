import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface InvestigationLoadErrorProps {
  message?: string;
  onRetry?: () => void;
}

export function InvestigationLoadError({
  message,
  onRetry,
}: InvestigationLoadErrorProps) {
  return (
    <div
      className="flex h-full flex-col items-center justify-center gap-4 p-6"
      role="alert"
    >
      <AlertCircle className="h-12 w-12 text-destructive" />
      <p className="text-lg font-medium text-text-primary">
        Failed to load investigation
      </p>
      <p className="text-sm text-text-muted">
        {message ?? "An error occurred while loading the investigation."}
      </p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
