import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getReadingStatus, setReadingStatus } from "../services/readingStatus";
import type { ReadingStatusSetRequest } from "../types/readingStatus";

export function useReadingStatus(
  investigationId: string | undefined,
  paperId: string | undefined,
) {
  return useQuery({
    queryKey: ["investigations", investigationId, "reading-status", paperId],
    queryFn: () => getReadingStatus(investigationId!, paperId!),
    enabled: !!investigationId && !!paperId,
  });
}

export function useSetReadingStatus(investigationId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      paperId,
      body,
    }: {
      paperId: string;
      body: ReadingStatusSetRequest;
    }) => setReadingStatus(investigationId!, paperId, body),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "reading-status", variables.paperId],
      });
    },
  });
}
