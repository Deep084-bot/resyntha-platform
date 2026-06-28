import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  useCreateInvestigation,
  useInvestigations,
} from "@/hooks/useInvestigations";
import { mapInvestigationStatus, type Investigation } from "@/types";

export function InvestigationsPage() {
  const { data: investigations, isLoading, isError } = useInvestigations();
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);

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
        <Button onClick={() => setShowModal(true)}>
          <Plus className="h-4 w-4" />
          New Investigation
        </Button>
      </div>

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
                  onClick={() => setShowModal(true)}
                >
                  <Plus className="h-4 w-4" />
                  New Investigation
                </Button>
              }
            />
          ) : (
            <div className="space-y-2">
              {filtered.map((inv) => (
                <InvestigationRow key={inv.id} investigation={inv} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showModal && (
        <CreateModal
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}

function InvestigationRow({
  investigation,
}: {
  investigation: Investigation;
}) {
  return (
    <Link
      to={`/investigations/${investigation.id}`}
      className="flex items-center justify-between rounded-lg border border-border bg-surface-card px-4 py-3 transition-colors hover:bg-surface-hover"
    >
      <div className="min-w-0 flex-1">
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
      </div>
      <StatusBadge
        status={mapInvestigationStatus(investigation.status)}
        label={investigation.status}
      />
    </Link>
  );
}

function CreateModal({ onClose }: { onClose: () => void }) {
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
        onSuccess: () => onClose(),
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
