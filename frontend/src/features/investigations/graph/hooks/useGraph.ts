import { useQuery } from "@tanstack/react-query";

import { fetchGraph } from "../services/graph";
import type { GraphDTO } from "../types/graph";

export interface UseGraphResult {
  data?: GraphDTO;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  isEmpty: boolean;
}

export function useGraph(investigationId: string | undefined): UseGraphResult {
  const query = useQuery<GraphDTO>({
    queryKey: ["investigations", investigationId, "graph"],
    queryFn: () => fetchGraph(investigationId!),
    enabled: !!investigationId,
    staleTime: 30_000,
  });

  const isEmpty =
    !query.isLoading &&
    !query.isError &&
    !!query.data &&
    query.data.nodes.length === 0;

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error instanceof Error ? query.error : null,
    isEmpty,
  };
}
