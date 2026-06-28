import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchExecution, fetchExecutionStages, fetchExecutions } from "@/services/executions";
import { triggerRetrieval } from "@/services/retrieval";
import type {
  Execution,
  ExecutionStage,
  RetrieveAcceptedResponse,
  RetrieveRequest,
} from "@/types";
import {
  isExecutionTerminal,
  queryKeys,
} from "@/types";

export function useExecutions(investigationId: string | undefined) {
  return useQuery<Execution[]>({
    queryKey: queryKeys.executions.byInvestigation(investigationId!),
    queryFn: () => fetchExecutions(investigationId!),
    enabled: !!investigationId,
  });
}

export function useLatestExecution(investigationId: string | undefined) {
  return useQuery<Execution[]>({
    queryKey: queryKeys.executions.byInvestigation(investigationId!),
    queryFn: () => fetchExecutions(investigationId!),
    enabled: !!investigationId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || data.length === 0) return 2000;
      const latest = data[0];
      if (latest && isExecutionTerminal(latest.status)) return false;
      return 2000;
    },
  });
}

export function useExecution(executionId: string | undefined) {
  return useQuery<Execution>({
    queryKey: queryKeys.executions.detail(executionId!),
    queryFn: () => fetchExecution(executionId!),
    enabled: !!executionId,
  });
}

export function useExecutionStages(executionId: string | undefined) {
  return useQuery<ExecutionStage[]>({
    queryKey: queryKeys.executions.stages(executionId!),
    queryFn: () => fetchExecutionStages(executionId!),
    enabled: !!executionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || data.length === 0) return 2000;
      const hasRunning = data.some((s) => s.status === "running" || s.status === "pending");
      return hasRunning ? 2000 : false;
    },
  });
}

export function useTriggerRetrievalWithPoll(investigationId: string) {
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
      qc.invalidateQueries({
        queryKey: queryKeys.executions.byInvestigation(investigationId),
      });
    },
  });
}
