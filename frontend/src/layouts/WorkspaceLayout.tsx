import { Link, Outlet, useLocation, useParams } from "react-router-dom";
import { ChevronRight } from "lucide-react";

import {
  Workspace,
  WorkspaceBody,
  WorkspaceHeader,
} from "@/components/layout";
import { PageTitle } from "@/components/layout/PageTitle";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useInvestigation } from "@/hooks/useInvestigations";
import { cn } from "@/lib/utils";
import { mapInvestigationStatus } from "@/types";

const tabs = [
  { label: "Overview", to: "" },
  { label: "Timeline", to: "timeline" },
  { label: "Artifacts", to: "artifacts" },
  { label: "Papers", to: "papers" },
  { label: "Validation", to: "validation" },
  { label: "Knowledge", to: "knowledge" },
  { label: "Executions", to: "executions" },
  { label: "Analysis", to: "analysis" },
  { label: "Gaps", to: "gaps" },
  { label: "Copilot", to: "copilot" },
] as const;

function ChevronRightIcon({ className }: { className?: string }) {
  return <ChevronRight className={cn("h-3 w-3", className)} />;
}

export function WorkspaceLayout() {
  const { id } = useParams();
  const location = useLocation();
  const { data: investigation, isLoading, isError } = useInvestigation(id);

  const activeTab = tabs.findIndex(
    (tab) =>
      location.pathname.endsWith(`/investigations/${id}/${tab.to}`) ||
      (tab.to === "" && location.pathname === `/investigations/${id}`),
  );

  if (isLoading) {
    return (
      <Workspace>
        <div className="border-b border-border px-6 pt-4 pb-0 space-y-4">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-6 w-96" />
          <Skeleton className="h-4 w-64" />
          <div className="flex gap-6 pb-2">
            {tabs.map((t) => (
              <Skeleton key={t.label} className="h-8 w-20" />
            ))}
          </div>
        </div>
        <WorkspaceBody>
          <Outlet />
        </WorkspaceBody>
      </Workspace>
    );
  }

  if (isError || !investigation) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
        <p className="text-lg font-medium text-text-primary">
          Investigation not found
        </p>
        <p className="text-sm text-text-muted">
          The investigation you're looking for doesn't exist or has been
          deleted.
        </p>
        <Link
          to="/"
          className="text-sm text-accent-default hover:underline"
        >
          Back to Investigations
        </Link>
      </div>
    );
  }

  return (
    <Workspace>
      <WorkspaceHeader>
        {/* Breadcrumb */}
        <nav className="mb-3 flex items-center gap-1.5 text-xs text-text-muted">
          <Link
            to="/"
            className="transition-colors hover:text-text-secondary"
          >
            Investigations
          </Link>
          <ChevronRightIcon />
          <span className="max-w-[200px] truncate text-text-primary">
            {investigation.title}
          </span>
        </nav>

        {/* Title row */}
        <div className="flex items-center gap-3">
          <PageTitle>{investigation.title}</PageTitle>
          <StatusBadge
            status={mapInvestigationStatus(investigation.status)}
            label={investigation.status}
          />
        </div>
        <p className="mb-4 mt-1 text-sm text-text-muted">
          {investigation.topic}
        </p>

        {/* Tabs */}
        <div className="flex gap-0">
          {tabs.map((tab, i) => {
            const href = tab.to
              ? `/investigations/${id}/${tab.to}`
              : `/investigations/${id}`;
            return (
              <Link
                key={tab.label}
                to={href}
                className={cn(
                  "relative px-4 py-2.5 text-sm font-medium transition-colors",
                  i === activeTab
                    ? "text-text-primary"
                    : "text-text-muted hover:text-text-secondary",
                )}
              >
                {tab.label}
                {i === activeTab && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-accent-default" />
                )}
              </Link>
            );
          })}
        </div>
      </WorkspaceHeader>

      <WorkspaceBody>
        <Outlet />
      </WorkspaceBody>
    </Workspace>
  );
}
