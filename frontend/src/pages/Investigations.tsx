import { Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";

export function InvestigationsPage() {
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
        <Button>
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
          className="w-full rounded-md border border-input bg-surface-card py-2 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* List */}
      <Card>
        <CardHeader>
          <CardTitle>All Investigations</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="No investigations yet"
            description="Create an investigation to begin collecting and analyzing research papers."
            action={<Button variant="outline"><Plus className="h-4 w-4" />New Investigation</Button>}
          />
        </CardContent>
      </Card>

      {/* Placeholder list items to show the pattern */}
      <div className="space-y-2 hidden">
        <InvestigationRow title="Attention Mechanisms in Transformers" status="running" />
        <InvestigationRow title="Graph Neural Networks for Drug Discovery" status="success" />
        <InvestigationRow title="Efficient Fine-Tuning of LLMs" status="pending" />
      </div>
    </div>
  );
}

function InvestigationRow({ title, status }: { title: string; status: "running" | "success" | "pending" }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-surface-card px-4 py-3 transition-colors hover:bg-surface-hover">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text-primary truncate">{title}</p>
        <p className="text-xs text-text-muted mt-0.5">Created 2 days ago</p>
      </div>
      <StatusBadge status={status} />
    </div>
  );
}
