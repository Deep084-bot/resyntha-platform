import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

import { useInvestigationRun } from "./InvestigationRunContext";

export interface RunAgainButtonProps {
  /**
   * When true, the investigation has already completed at least once and
   * the button should read "Re-run".
   */
  hasCompletedExecution?: boolean;
  className?: string;
}

/**
 * Reusable investigation action button. The label is derived from the
 * current run state in one place so pages do not duplicate the decision.
 */
export function RunAgainButton({
  hasCompletedExecution = false,
  className,
}: RunAgainButtonProps) {
  const { run, isStarting, running } = useInvestigationRun();
  const disabled = isStarting || running;

  const label = isStarting || running
    ? "Running Investigation..."
    : hasCompletedExecution
      ? "Re-run"
      : "Run Investigation";

  return (
    <Button
      onClick={run}
      disabled={disabled}
      variant={hasCompletedExecution ? "outline" : "default"}
      size="sm"
      className={className}
      aria-label={label}
    >
      {isStarting || running ? (
        <Spinner size="sm" className="mr-2 border-t-current" />
      ) : (
        <RefreshCw className="mr-1.5 h-4 w-4" />
      )}
      {label}
    </Button>
  );
}
