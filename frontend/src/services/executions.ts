import api from "@/lib/api";
import type { Execution, ExecutionStage } from "@/types";

export async function fetchExecutions(
  investigationId: string,
): Promise<Execution[]> {
  const { data } = await api.get<Execution[]>(
    `/investigations/${investigationId}/executions`,
  );
  return data;
}

export async function fetchExecution(
  executionId: string,
): Promise<Execution> {
  const { data } = await api.get<Execution>(`/executions/${executionId}`);
  return data;
}

export async function fetchExecutionStages(
  executionId: string,
): Promise<ExecutionStage[]> {
  const { data } = await api.get<ExecutionStage[]>(
    `/executions/${executionId}/stages`,
  );
  return data;
}
