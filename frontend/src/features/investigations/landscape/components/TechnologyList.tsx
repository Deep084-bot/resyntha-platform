import { Cpu } from "lucide-react";

import type { Technology } from "../types";

export interface TechnologyListProps {
  technologies: Technology[];
}

export function TechnologyList({ technologies }: TechnologyListProps) {
  if (technologies.length === 0) {
    return (
      <p className="text-sm text-text-muted">
        No technology data available.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {technologies.map((t) => (
        <div
          key={t.name}
          className="flex items-center justify-between rounded-lg border border-border bg-surface-active/30 px-3 py-2.5"
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <Cpu className="h-4 w-4 shrink-0 text-text-muted" />
            <span className="truncate text-sm font-medium text-text-primary">
              {t.name}
            </span>
          </div>
          <div className="flex items-center gap-4 shrink-0 ml-4">
            {t.first_appearance_year && (
              <div className="text-right">
                <p className="text-sm font-semibold text-text-primary">
                  {t.first_appearance_year}
                </p>
                <p className="text-[10px] text-text-muted">first year</p>
              </div>
            )}
            <div className="text-right">
              <p className="text-sm font-semibold text-text-primary">
                {t.paper_count}
              </p>
              <p className="text-[10px] text-text-muted">papers</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
