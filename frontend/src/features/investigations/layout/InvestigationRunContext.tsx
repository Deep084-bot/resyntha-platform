import { createContext, useContext } from "react";

import type { Execution, ExecutionStage } from "@/types";

export interface InvestigationRunContextValue {
  /**
   * True when at least one execution on this investigation is pending or
   * running. The UI uses this to suppress empty states across every tab.
   */
  running: boolean;
  /** Most recent execution (newest first as returned by the backend). */
  latestExecution: Execution | null;
  /** Stages for `latestExecution`. Empty array while the stages call is loading. */
  stages: ExecutionStage[];
  /** Trigger a new run. The mutation is the existing useRunInvestigation. */
  run: () => void;
  /** True while the mutation POST is in flight. */
  isStarting: boolean;
  /**
   * Error from the most recent run attempt (if any). Cleared on next click.
   */
  error: string | null;
}

const InvestigationRunContext = createContext<InvestigationRunContextValue | null>(
  null,
);

export const InvestigationRunContextProvider = InvestigationRunContext.Provider;

export function useInvestigationRun(): InvestigationRunContextValue {
  const value = useContext(InvestigationRunContext);
  if (!value) {
    throw new Error(
      "useInvestigationRun must be used within an InvestigationRunContextProvider",
    );
  }
  return value;
}
