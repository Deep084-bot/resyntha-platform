import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Outlet, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Bot } from "lucide-react";

import {
  Workspace,
  WorkspaceBody,
  WorkspaceHeader,
} from "@/components/layout";
import {
  useInvestigation,
  useDeleteInvestigation,
} from "@/hooks/useInvestigations";
import {
  useExecutions,
  useExecutionStages,
  useRunInvestigation,
} from "@/hooks/useExecutions";
import {
  isExecutionTerminal,
  queryKeys,
  type Execution,
  type ExecutionStage,
  type Investigation,
} from "@/types";
import { useBreadcrumbStore } from "@/stores/breadcrumbs";

import { DeleteConfirmationDialog } from "../components/DeleteConfirmationDialog";
import { InvestigationSkeleton } from "../components/InvestigationSkeleton";
import { InvestigationNotFound } from "../components/InvestigationNotFound";
import { InvestigationLoadError } from "../components/InvestigationLoadError";
import { WorkspaceErrorBoundary } from "../components/WorkspaceErrorBoundary";
import { InvestigationHeader } from "./InvestigationHeader";
import { InvestigationTabs } from "./InvestigationTabs";
import { InvestigationProgressBanner } from "./InvestigationProgressBanner";
import {
  InvestigationRunContextProvider,
  type InvestigationRunContextValue,
} from "./InvestigationRunContext";

const TABS = [
  { label: "Overview", to: "" },
  { label: "Papers", to: "papers" },
  { label: "Landscape", to: "landscape" },
  { label: "Graph", to: "graph" },
  { label: "Notes", to: "notes" },
  { label: "Artifacts", to: "artifacts" },
  { label: "Executions", to: "executions" },
] as const;

export function InvestigationLayout() {
  const { id } = useParams();
  const { data: investigation, isLoading, isError } = useInvestigation(id);
  const deleteMutation = useDeleteInvestigation();
  const setBreadcrumbLabel = useBreadcrumbStore((s) => s.setLabel);
  const clearBreadcrumbLabel = useBreadcrumbStore((s) => s.clearLabel);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Update breadcrumb when investigation loads
  useEffect(() => {
    if (investigation?.title && id) {
      setBreadcrumbLabel(id, investigation.title);
    }
    return () => {
      if (id) clearBreadcrumbLabel(id);
    };
  }, [investigation?.title, id, setBreadcrumbLabel, clearBreadcrumbLabel]);

  if (isLoading) {
    return (
      <Workspace>
        <InvestigationSkeleton />
      </Workspace>
    );
  }

  if (isError || !investigation) {
    return (
      <Workspace>
        {isError && investigation === undefined ? (
          <InvestigationLoadError />
        ) : (
          <InvestigationNotFound />
        )}
      </Workspace>
    );
  }

  return (
    <Workspace>
      <InvestigationWorkspaceContent
        investigation={investigation}
        onRequestDelete={() => setShowDeleteDialog(true)}
        isDeleting={deleteMutation.isPending}
      />

      {showDeleteDialog && (
        <DeleteConfirmationDialog
          investigation={investigation}
          isPending={deleteMutation.isPending}
          onConfirm={() => {
            deleteMutation.mutate(investigation.id, {
              onSuccess: () => setShowDeleteDialog(false),
            });
          }}
          onClose={() => {
            setShowDeleteDialog(false);
            deleteMutation.reset();
          }}
          error={
            deleteMutation.isError ? deleteMutation.error.message : null
          }
        />
      )}
    </Workspace>
  );
}

interface InvestigationWorkspaceContentProps {
  investigation: Investigation;
  onRequestDelete: () => void;
  isDeleting: boolean;
}

function InvestigationWorkspaceContent({
  investigation,
  onRequestDelete,
  isDeleting,
}: InvestigationWorkspaceContentProps) {
  const investigationId = investigation.id;
  const qc = useQueryClient();
  const { data: executions } = useExecutions(investigationId);
  const runInvestigation = useRunInvestigation(investigationId);

  const latestExecution: Execution | null =
    executions?.[0] ?? null;
  const hasCompletedExecution = (executions ?? []).some(
    (e) => e.status === "completed",
  );

  const stagesResult = useExecutionStages(latestExecution?.id);
  const stages: ExecutionStage[] = stagesResult.data ?? [];
  const copilotUnlocked = investigation.status === "completed";

  // True when any execution is still pending or running.
  const running = useMemo(
    () => (executions ?? []).some((e) => !isExecutionTerminal(e.status)),
    [executions],
  );

  // Track terminal transitions to refresh sibling queries so the tabs
  // auto-populate as soon as data is ready.
  const lastSeenStatusRef = useRef<Execution["status"] | null>(null);
  useEffect(() => {
    if (!latestExecution) {
      lastSeenStatusRef.current = null;
      return;
    }
    const prev = lastSeenStatusRef.current;
    const current = latestExecution.status;
    const justTerminalized =
      prev !== null && !isExecutionTerminal(prev) && isExecutionTerminal(current);
    if (justTerminalized) {
      qc.invalidateQueries({
        queryKey: queryKeys.investigations.timeline(investigationId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.papers.byInvestigation(investigationId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.artifacts.byInvestigation(investigationId),
      });
      qc.invalidateQueries({
        queryKey: ["investigations", investigationId, "landscape"],
      });
      qc.invalidateQueries({
        queryKey: queryKeys.investigations.detail(investigationId),
      });
      qc.invalidateQueries({
        queryKey: queryKeys.graph.byInvestigation(investigationId),
      });
    }
    lastSeenStatusRef.current = current;
  }, [latestExecution, investigationId, qc]);

  const handleRun = useCallback(() => {
    if (!investigation.topic) return;
    runInvestigation.mutate({
      query: investigation.topic,
      paper_limit: investigation.paper_limit,
    });
  }, [runInvestigation, investigation.topic, investigation.paper_limit]);

  const runContextValue: InvestigationRunContextValue = {
    running,
    latestExecution,
    stages,
    run: handleRun,
    isStarting: runInvestigation.isPending,
    error: runInvestigation.isError
      ? (runInvestigation.error?.message ?? "Failed to start pipeline")
      : null,
  };

  return (
    <InvestigationRunContextProvider value={runContextValue}>
      <WorkspaceHeader>
        <InvestigationHeader
          investigation={investigation}
          onDelete={onRequestDelete}
          isDeleting={isDeleting}
          hasCompletedExecution={hasCompletedExecution}
        />
        <div className="mt-4">
          <InvestigationTabs
            tabs={[
              ...TABS,
              {
                label: "Copilot",
                to: "copilot",
                disabled: !copilotUnlocked,
                tooltip: !copilotUnlocked
                  ? "Complete an investigation to unlock AI Copilot."
                  : undefined,
                icon: Bot,
              },
            ]}
          />
        </div>
        {latestExecution && (
          <div className="mt-4">
            <InvestigationProgressBanner
              execution={latestExecution}
              stages={stages}
            />
          </div>
        )}
      </WorkspaceHeader>

      <WorkspaceBody>
        <WorkspaceErrorBoundary>
          <Outlet context={{ investigation }} />
        </WorkspaceErrorBoundary>
      </WorkspaceBody>
    </InvestigationRunContextProvider>
  );
}
