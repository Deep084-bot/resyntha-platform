import { AlertCircle, RefreshCw } from "lucide-react";

export interface ExecutionErrorStateProps {
  onRetry?: () => void;
}

export function ExecutionErrorState({
  onRetry,
}: ExecutionErrorStateProps) {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-md border border-destructive/20 bg-destructive/5 px-4">
      <AlertCircle className="h-8 w-8 text-destructive" />
      <div className="text-center">
        <p className="text-sm font-medium text-destructive">
          Failed to load execution data
        </p>
        <p className="mt-1 text-xs text-text-muted">
          An error occurred while fetching execution details.
        </p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="flex items-center gap-1.5 rounded-md bg-destructive px-3 py-1.5 text-xs font-medium text-white hover:bg-destructive/90"
        >
          <RefreshCw className="h-3 w-3" />
          Retry
        </button>
      )}
    </div>
  );
}
