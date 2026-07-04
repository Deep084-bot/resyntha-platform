import { useQuery } from "@tanstack/react-query";

import { fetchLandscape } from "../services/landscape";
import type { LandscapeData } from "../types";

export function useLandscape(investigationId: string | undefined) {
  return useQuery<LandscapeData>({
    queryKey: ["investigations", investigationId, "landscape"],
    queryFn: () => fetchLandscape(investigationId!),
    enabled: !!investigationId,
  });
}
