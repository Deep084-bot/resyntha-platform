import { useState, useCallback } from "react";

import { useArtifacts } from "@/hooks/useArtifacts";

export function useArtifactsPage(investigationId: string | undefined) {
  const { data: artifacts, isLoading, isError, refetch } =
    useArtifacts(investigationId);

  const [selectedId, setSelectedId] = useState<string | undefined>();

  const selected = artifacts?.find((a) => a.id === selectedId) ?? null;

  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  return {
    artifacts: artifacts ?? [],
    selected,
    selectedId: selected?.id,
    isLoading,
    isError,
    handleSelect,
    handleRefresh,
  };
}
