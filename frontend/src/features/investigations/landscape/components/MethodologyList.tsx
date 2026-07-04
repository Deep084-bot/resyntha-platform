import { FlaskConical } from "lucide-react";

import type { Methodology } from "../types";

export interface MethodologyListProps {
  methodologies: Methodology[];
}

export function MethodologyList({ methodologies }: MethodologyListProps) {
  if (methodologies.length === 0) {
    return (
      <p className="text-sm text-text-muted">
        No methodology data available.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {methodologies.map((m) => (
        <div
          key={m.name}
          className="flex items-center justify-between rounded-lg border border-border bg-surface-active/30 px-3 py-2.5"
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <FlaskConical className="h-4 w-4 shrink-0 text-text-muted" />
            <span className="truncate text-sm font-medium text-text-primary">
              {m.name}
            </span>
          </div>
          <div className="flex items-center gap-4 shrink-0 ml-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-text-primary">
                {m.technique_count}
              </p>
              <p className="text-[10px] text-text-muted">techniques</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-text-primary">
                {m.paper_count}
              </p>
              <p className="text-[10px] text-text-muted">papers</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
