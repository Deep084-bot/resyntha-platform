import { useEffect, useState } from "react";
import { Outlet, useParams } from "react-router-dom";

import {
  Workspace,
  WorkspaceBody,
  WorkspaceHeader,
} from "@/components/layout";
import { useInvestigation } from "@/hooks/useInvestigations";
import {
  useDeleteInvestigation,
} from "@/hooks/useInvestigations";
import { useBreadcrumbStore } from "@/stores/breadcrumbs";

import { DeleteConfirmationDialog } from "../components/DeleteConfirmationDialog";
import { InvestigationSkeleton } from "../components/InvestigationSkeleton";
import { InvestigationNotFound } from "../components/InvestigationNotFound";
import { InvestigationLoadError } from "../components/InvestigationLoadError";
import { InvestigationHeader } from "./InvestigationHeader";
import { InvestigationTabs } from "./InvestigationTabs";

const TABS = [
  { label: "Overview", to: "" },
  { label: "Papers", to: "papers" },
  { label: "Landscape", to: "landscape" },
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
      <WorkspaceHeader>
        <InvestigationHeader
          investigation={investigation}
          onDelete={() => setShowDeleteDialog(true)}
          isDeleting={deleteMutation.isPending}
        />
        <div className="mt-4">
          <InvestigationTabs tabs={[...TABS]} />
        </div>
      </WorkspaceHeader>

      <WorkspaceBody>
        <Outlet />
      </WorkspaceBody>

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
