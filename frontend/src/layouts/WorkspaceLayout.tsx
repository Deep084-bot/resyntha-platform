import { Link, Outlet, useLocation, useParams } from "react-router-dom";

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
] as const;

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
      <div className="flex h-full flex-col">
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
        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </div>
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
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border">
        <div className="px-6 pt-4 pb-0">
          {/* Breadcrumb */}
          <nav className="mb-3 flex items-center gap-1.5 text-xs text-text-muted">
            <Link
              to="/"
              className="hover:text-text-secondary transition-colors"
            >
              Investigations
            </Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-text-primary truncate max-w-[200px]">
              {investigation.title}
            </span>
          </nav>

          {/* Title row */}
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-text-primary">
              {investigation.title}
            </h1>
            <StatusBadge
              status={mapInvestigationStatus(investigation.status)}
              label={investigation.status}
            />
          </div>
          <p className="mt-1 mb-4 text-sm text-text-muted">
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
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-default rounded-full" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </div>
    </div>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m8.25 4.5 7.5 7.5-7.5 7.5"
      />
    </svg>
  );
}
