import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Bookmark, Plus, BookOpenCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  useCreateInvestigation,
  useDeleteInvestigation,
  useInvestigations,
} from "@/hooks/useInvestigations";
import { SectionHeader } from "@/components/ui/section-header";
import type { Investigation } from "@/types";

import {
  DeleteConfirmationDialog,
  InvestigationFilters,
  InvestigationList,
  InvestigationSearch,
  NewInvestigationDialog,
  QuickStats,
} from "../components";
import type { NewInvestigationForm } from "../components";
import { computeStats, filterInvestigations } from "../hooks";
import type { FilterState } from "../hooks";

const DEFAULT_FILTERS: FilterState = {
  status: "all",
  sort: "newest",
  search: "",
};

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: investigations = [], isLoading, isError } = useInvestigations();
  const createMutation = useCreateInvestigation();
  const deleteMutation = useDeleteInvestigation();

  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Investigation | null>(null);

  const stats = computeStats(investigations);
  const filtered = filterInvestigations(investigations, filters);

  const handleCreate = useCallback(
    (form: NewInvestigationForm) => {
      createMutation.mutate(
        {
          title: form.title.trim(),
          topic: form.topic.trim(),
          paper_limit: form.paperLimit ? Number(form.paperLimit) : undefined,
        },
        {
          onSuccess: (investigation) => {
            setShowCreateDialog(false);
            navigate(`/investigations/${investigation.id}`);
          },
        },
      );
    },
    [createMutation, navigate],
  );

  const handleDeleteConfirm = useCallback(() => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget.id, {
      onSuccess: () => {
        setDeleteTarget(null);
      },
    });
  }, [deleteTarget, deleteMutation]);

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* Welcome header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Welcome to Resyntha. Manage your research investigations.
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4" />
          New Investigation
        </Button>
      </div>

      {/* Quick stats */}
      <QuickStats stats={stats} />

      {/* Search and Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <InvestigationSearch
          value={filters.search}
          onChange={(search) => setFilters((prev) => ({ ...prev, search }))}
          className="sm:max-w-xs"
        />
        <InvestigationFilters
          filters={filters}
          onChange={setFilters}
        />
      </div>

      {/* Investigation list */}
      <section aria-labelledby="recent-heading">
        <SectionHeader
          title="Recent Investigations"
          description={
            !isLoading
              ? `${filtered.length} of ${investigations.length} investigation${investigations.length === 1 ? "" : "s"}`
              : undefined
          }
        />
        <div className="mt-4">
          <InvestigationList
            investigations={filtered}
            isLoading={isLoading}
            isError={isError}
            search={filters.search}
            onCreateNew={() => setShowCreateDialog(true)}
            onDelete={(inv) => setDeleteTarget(inv)}
          />
        </div>
      </section>

      {/* Recent Activity */}
      <section aria-labelledby="activity-heading">
        <h2
          id="activity-heading"
          className="text-lg font-semibold text-text-primary"
        >
          Recent Activity
        </h2>
        <div className="mt-4 space-y-2">
          {investigations.length > 0 ? (
            investigations.slice(0, 5).map((inv) => (
              <ActivityItem key={inv.id} investigation={inv} />
            ))
          ) : (
            <div className="rounded-lg border border-border bg-surface-card p-8 text-center">
              <p className="text-sm text-text-muted">
                Recent activity will appear here as you work on investigations.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Dialogs */}
      {showCreateDialog && (
        <NewInvestigationDialog
          isPending={createMutation.isPending}
          onSubmit={handleCreate}
          onClose={() => {
            setShowCreateDialog(false);
            createMutation.reset();
          }}
          error={createMutation.isError ? createMutation.error.message : null}
        />
      )}

      {deleteTarget && (
        <DeleteConfirmationDialog
          investigation={deleteTarget}
          isPending={deleteMutation.isPending}
          onConfirm={handleDeleteConfirm}
          onClose={() => {
            setDeleteTarget(null);
            deleteMutation.reset();
          }}
          error={deleteMutation.isError ? deleteMutation.error.message : null}
        />
      )}
    </div>
  );
}

/* ── Recent Activity Item ──────────────────────────────────── */

interface ActivityItemProps {
  investigation: Investigation;
}

function ActivityItem({ investigation }: ActivityItemProps) {
  const navigate = useNavigate();
  const statusIcon = {
    completed: BookOpenCheck,
    running: Bookmark,
    default: FileText,
  } as const;
  const Icon = statusIcon[investigation.status as keyof typeof statusIcon] ?? FileText;

  return (
    <button
      type="button"
      onClick={() => navigate(`/investigations/${investigation.id}`)}
      className="flex w-full items-center gap-3 rounded-lg border border-border bg-surface-card p-3 text-left transition-colors hover:bg-surface-hover"
    >
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-default/10">
        <Icon className="h-4 w-4 text-accent-default" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">
          {investigation.title}
        </p>
        <p className="text-xs text-text-muted">
          {investigation.status === "completed"
            ? "Investigation completed"
            : investigation.status === "failed"
              ? "Investigation failed"
              : `Status: ${investigation.status}`}
        </p>
      </div>
      <span className="text-xs text-text-muted shrink-0">
        {new Date(investigation.updated_at).toLocaleDateString()}
      </span>
    </button>
  );
}
