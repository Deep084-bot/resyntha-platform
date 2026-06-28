import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchPapers, triggerRetrieval } from "@/services/retrieval";
import type { Paper, RetrieveAcceptedResponse, RetrieveRequest } from "@/types";
import { queryKeys } from "@/types";

export function usePapers(investigationId: string | undefined) {
  return useQuery<Paper[]>({
    queryKey: queryKeys.papers.byInvestigation(investigationId!),
    queryFn: () => fetchPapers(investigationId!),
    enabled: !!investigationId,
  });
}

export function useTriggerRetrieval(investigationId: string) {
  const qc = useQueryClient();
  return useMutation<
    RetrieveAcceptedResponse,
    Error,
    RetrieveRequest
  >({
    mutationFn: (body) => triggerRetrieval(investigationId, body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: queryKeys.papers.byInvestigation(investigationId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.investigations.timeline(investigationId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.artifacts.byInvestigation(investigationId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.investigations.detail(investigationId),
      });
    },
  });
}
