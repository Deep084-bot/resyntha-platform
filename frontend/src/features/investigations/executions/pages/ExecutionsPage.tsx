import { useParams } from "react-router-dom";

import { useExecutionsPage } from "../hooks/useExecutionsPage";
import { SectionHeader } from "@/components/ui/section-header";

import { ExecutionHistory } from "../components/ExecutionHistory";
import { ExecutionTimeline } from "../components/ExecutionTimeline";
import { ExecutionProgress } from "../components/ExecutionProgress";
import { ExecutionMetrics } from "../components/ExecutionMetrics";
import { ExecutionLogPreview } from "../components/ExecutionLogPreview";
import { ExecutionSkeleton } from "../components/ExecutionSkeleton";
import { ExecutionErrorState } from "../components/ExecutionErrorState";
import { ExecutionEmptyState } from "../components/ExecutionEmptyState";

export function ExecutionsPage() {
  const { id } = useParams();
  const { executions, selectedId, setSelectedId, isLoading, isError, stagesResult } =
    useExecutionsPage(id);

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        <SectionHeader title="Executions" />
        <ExecutionSkeleton />
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="space-y-4">
        <SectionHeader title="Executions" />
        <ExecutionErrorState />
      </div>
    );
  }

  // Empty state
  if (!executions || executions.length === 0) {
    return (
      <div className="space-y-4">
        <SectionHeader title="Executions" />
        <ExecutionEmptyState />
      </div>
    );
  }

  const selectedExecution = executions.find((e) => e.id === selectedId);
  const stages = stagesResult.data ?? [];

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Executions"
        description={`${executions.length} execution${executions.length === 1 ? "" : "s"} total`}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Sidebar: Execution history */}
        <div className="lg:col-span-1">
          <ExecutionHistory
            executions={executions}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>

        {/* Main: Selected execution details */}
        <div className="space-y-6 lg:col-span-2">
          {selectedExecution && (
            <>
              {/* Progress bar */}
              <ExecutionProgress
                execution={selectedExecution}
                stages={stages}
              />

              {/* Metrics grid */}
              <ExecutionMetrics
                execution={selectedExecution}
                stages={stages}
              />

              {/* Pipeline timeline */}
              <div>
                <h3 className="mb-3 text-xs font-medium text-text-muted uppercase tracking-wider">
                  Pipeline Stages
                </h3>
                {stagesResult.isLoading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="flex gap-4">
                        <div className="h-7 w-7 shrink-0 animate-pulse rounded-full bg-surface-active" />
                        <div className="flex-1 space-y-2">
                          <div className="h-4 w-48 animate-pulse rounded bg-surface-active" />
                          <div className="h-3 w-64 animate-pulse rounded bg-surface-active" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <ExecutionTimeline stages={stages} />
                )}
              </div>

              {/* Logs */}
              {stages.length > 0 && (
                <ExecutionLogPreview stages={stages} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
