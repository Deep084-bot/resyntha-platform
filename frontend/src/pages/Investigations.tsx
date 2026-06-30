import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MoreHorizontal, Plus, Search, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  useCreateInvestigation,
  useDeleteInvestigation,
  useInvestigations,
} from "@/hooks/useInvestigations";
import { mapInvestigationStatus, type Investigation } from "@/types";

export function InvestigationsPage() {
  const { data: investigations, isLoading, isError } = useInvestigations();
  const [search, setSearch] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Investigation | null>(null);
  const [deletedId, setDeletedId] = useState<string | null>(null);

  const filtered = (investigations ?? []).filter((inv) =>
    inv.title.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            Investigations
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Manage your research investigations
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4" />
          New Investigation
        </Button>
      </div>

      {/* Deleted confirmation banner */}
      {deletedId && (
        <div className="rounded-md border border-success/30 bg-success/5 px-4 py-3 text-sm text-success">
          Investigation deleted successfully.
          <button
            type="button"
            onClick={() => setDeletedId(null)}
            className="ml-2 underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="search"
          placeholder="Search investigations…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-md border border-input bg-surface-card py-2 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* List */}
      <Card>
        <CardHeader>
          <CardTitle>All Investigations</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full rounded-lg" />
              ))}
            </div>
          ) : isError ? (
            <p className="py-8 text-center text-sm text-destructive">
              Failed to load investigations. Check your connection and try
              again.
            </p>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No investigations yet"
              description="Create an investigation to begin collecting and analyzing research papers."
              action={
                <Button
                  variant="outline"
                  onClick={() => setShowCreateModal(true)}
                >
                  <Plus className="h-4 w-4" />
                  New Investigation
                </Button>
              }
            />
          ) : (
            <div className="space-y-2">
              {filtered.map((inv) => (
                <InvestigationRow
                  key={inv.id}
                  investigation={inv}
                  onDelete={() => setDeleteTarget(inv)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showCreateModal && (
        <CreateModal
          onClose={() => setShowCreateModal(false)}
        />
      )}

      {deleteTarget && (
        <DeleteConfirmModal
          investigation={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDeleted={(id) => {
            setDeleteTarget(null);
            setDeletedId(id);
          }}
        />
      )}
    </div>
  );
}

function InvestigationRow({
  investigation,
  onDelete,
}: {
  investigation: Investigation;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  return (
    <div className="relative flex items-center justify-between rounded-lg border border-border bg-surface-card px-4 py-3 transition-colors hover:bg-surface-hover">
      <Link
        to={`/investigations/${investigation.id}`}
        className="min-w-0 flex-1"
      >
        <p className="text-sm font-medium text-text-primary truncate">
          {investigation.title}
        </p>
        <p className="text-xs text-text-muted mt-0.5">
          {new Date(investigation.created_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </p>
      </Link>
      <div className="flex items-center gap-2 shrink-0">
        <StatusBadge
          status={mapInvestigationStatus(investigation.status)}
          label={investigation.status}
        />
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((prev) => !prev);
            }}
            className="rounded-md p-1 text-text-muted hover:text-text-primary hover:bg-surface-active"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-full z-50 mt-1 w-44 overflow-hidden rounded-md border border-border bg-surface-card shadow-lg">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpen(false);
                  onDelete();
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4" />
                Delete Investigation
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DeleteConfirmModal({
  investigation,
  onClose,
  onDeleted,
}: {
  investigation: Investigation;
  onClose: () => void;
  onDeleted: (id: string) => void;
}) {
  const navigate = useNavigate();
  const deleteMutation = useDeleteInvestigation();

  const handleDelete = () => {
    deleteMutation.mutate(investigation.id, {
      onSuccess: () => {
        onDeleted(investigation.id);
        const currentPath = window.location.pathname;
        if (currentPath.startsWith(`/investigations/${investigation.id}`)) {
          navigate("/", { replace: true });
        }
      },
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface-card p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">
            Delete Investigation
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-text-muted hover:text-text-primary"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm text-text-primary">
            <p className="font-medium">{investigation.title}</p>
          </div>
          <p className="text-sm text-text-muted">
            This will permanently delete this investigation and all associated
            data including papers, artifacts, timeline events, execution
            history, and knowledge extraction results. This action cannot be
            undone.
          </p>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Spinner size="sm" className="border-t-white" />
                  Deleting…
                </>
              ) : (
                "Delete"
              )}
            </Button>
          </div>
          {deleteMutation.isError && (
            <p className="text-xs text-destructive">
              {deleteMutation.error.message}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function CreateModal({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const titleRef = useRef<HTMLInputElement>(null);
  const topicRef = useRef<HTMLTextAreaElement>(null);
  const limitRef = useRef<HTMLInputElement>(null);
  const create = useCreateInvestigation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const title = titleRef.current?.value.trim();
    const topic = topicRef.current?.value.trim();
    if (!title || !topic) return;

    create.mutate(
      {
        title,
        topic,
        paper_limit: limitRef.current?.value
          ? Number(limitRef.current.value)
          : undefined,
      },
      {
        onSuccess: (investigation) => {
          onClose();
          navigate(`/investigations/${investigation.id}`);
        },
      },
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border border-border bg-surface-card p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">
            New Investigation
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-text-muted hover:text-text-primary"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Title
            </label>
            <input
              ref={titleRef}
              required
              className="w-full rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="e.g. Attention Mechanisms in Transformers"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Topic
            </label>
            <textarea
              ref={topicRef}
              required
              rows={3}
              className="w-full rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              placeholder="Describe the research topic…"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Paper limit
            </label>
            <input
              ref={limitRef}
              type="number"
              min={1}
              max={100}
              defaultValue={10}
              className="w-full rounded-md border border-input bg-surface-base px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={create.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? (
                <>
                  <Spinner size="sm" className="border-t-white" />
                  Creating…
                </>
              ) : (
                "Create"
              )}
            </Button>
          </div>
          {create.isError && (
            <p className="text-xs text-destructive">
              {create.error.message}
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
