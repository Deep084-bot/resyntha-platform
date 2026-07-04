import { useEffect, useState } from "react";

import { useExecutions, useExecutionStages } from "@/hooks/useExecutions";

export function useExecutionsPage(investigationId: string | undefined) {
  const {
    data: executions,
    isLoading,
    isError,
  } = useExecutions(investigationId);

  const latest = executions?.[0];
  const [selectedId, setSelectedId] = useState<string | undefined>(
    latest?.id,
  );

  // Sync selected ID to latest execution when data first loads
  useEffect(() => {
    if (latest && !selectedId) {
      setSelectedId(latest.id);
    }
  }, [latest, selectedId]);

  const resolvedId = selectedId ?? latest?.id;
  const stagesResult = useExecutionStages(resolvedId);

  return {
    executions,
    selectedId: resolvedId,
    setSelectedId,
    isLoading,
    isError,
    stagesResult,
  };
}
