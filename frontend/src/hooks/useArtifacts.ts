import { useQuery } from "@tanstack/react-query";

import { fetchArtifacts } from "@/services/artifacts";
import type { Artifact } from "@/types";
import { queryKeys } from "@/types";

export function useArtifacts(investigationId: string | undefined) {
  return useQuery<Artifact[]>({
    queryKey: queryKeys.artifacts.byInvestigation(investigationId!),
    queryFn: () => fetchArtifacts(investigationId!),
    enabled: !!investigationId,
  });
}
