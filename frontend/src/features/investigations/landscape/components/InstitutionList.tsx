import { Building2 } from "lucide-react";

import type { Institution } from "../types";

export interface InstitutionListProps {
  institutions: Institution[];
}

function InstitutionTypeBadge({ type }: { type: string }) {
  return (
    <span className="rounded bg-surface-active px-1.5 py-0.5 text-[10px] font-medium text-text-muted">
      {type}
    </span>
  );
}

export function InstitutionList({ institutions }: InstitutionListProps) {
  if (institutions.length === 0) {
    return (
      <p className="text-sm text-text-muted">No institution data available.</p>
    );
  }

  return (
    <div className="space-y-2">
      {institutions.map((inst) => (
        <div
          key={inst.name}
          className="flex items-center justify-between rounded-lg border border-border bg-surface-active/30 px-3 py-2.5"
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <Building2 className="h-4 w-4 shrink-0 text-text-muted" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text-primary">
                {inst.name}
              </p>
              <InstitutionTypeBadge type={inst.type} />
            </div>
          </div>
          <div className="flex items-center gap-4 shrink-0 ml-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-text-primary">
                {inst.paper_count}
              </p>
              <p className="text-[10px] text-text-muted">papers</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-text-primary">
                {inst.author_count}
              </p>
              <p className="text-[10px] text-text-muted">authors</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
