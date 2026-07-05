import { useQuery } from "@tanstack/react-query";

import { fetchLandscape } from "../services/landscape";
import type { LandscapeData } from "../types";
import { AppError } from "@/api/errors";

export interface UseLandscapeResult {
  data?: LandscapeData;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  isNotGenerated: boolean;
}

export function useLandscape(investigationId: string | undefined): UseLandscapeResult {
  const query = useQuery<LandscapeData>({
    queryKey: ["investigations", investigationId, "landscape"],
    queryFn: () => fetchLandscape(investigationId!),
    enabled: !!investigationId,
  });

  const isNotGenerated =
    query.isError &&
    query.error instanceof AppError &&
    query.error.kind === "not_found";

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError && !isNotGenerated,
    error: !isNotGenerated ? query.error : null,
    isNotGenerated,
  };
}
