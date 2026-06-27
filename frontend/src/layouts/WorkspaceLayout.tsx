import { Link, Outlet, useLocation, useParams } from "react-router-dom";

import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

const tabs = [
  { label: "Overview", to: "" },
  { label: "Timeline", to: "timeline" },
  { label: "Artifacts", to: "artifacts" },
  { label: "Papers", to: "papers" },
  { label: "Analysis", to: "analysis" },
] as const;

/**
 * Persistent workspace shell for viewing a single investigation.
 *
 * Renders:
 * - Breadcrumb navigation
 * - Investigation name + status badge
 * - Tab bar for switching between views
 * - Content area via nested <Outlet />
 */
export function WorkspaceLayout() {
  const { id } = useParams();
  const location = useLocation();

  const activeTab = tabs.findIndex(
    (tab) =>
      location.pathname.endsWith(`/workspace/${id}/${tab.to}`) ||
      (tab.to === "" && location.pathname === `/workspace/${id}`),
  );

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border">
        <div className="px-6 pt-4 pb-0">
          {/* Breadcrumb */}
          <nav className="mb-3 flex items-center gap-1.5 text-xs text-text-muted">
            <Link to="/" className="hover:text-text-secondary transition-colors">
              Investigations
            </Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-text-primary truncate max-w-[200px]">
              Investigation {id?.slice(0, 8)}
            </span>
          </nav>

          {/* Title row */}
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-text-primary">
              Investigating Attention Mechanisms in Transformer Architectures
            </h1>
            <StatusBadge status="running" label="In Progress" />
          </div>
          <p className="mt-1 mb-4 text-sm text-text-muted">
            Understanding how attention mechanisms influence transformer performance
            across NLP and vision tasks.
          </p>

          {/* Tabs */}
          <div className="flex gap-0">
            {tabs.map((tab, i) => {
              const href = tab.to
                ? `/workspace/${id}/${tab.to}`
                : `/workspace/${id}`;
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
