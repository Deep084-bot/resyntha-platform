import { Database } from "lucide-react";

import type { Dataset } from "../types";

export interface DatasetListProps {
  datasets: Dataset[];
}

export function DatasetList({ datasets }: DatasetListProps) {
  if (datasets.length === 0) {
    return (
      <p className="text-sm text-text-muted">No dataset data available.</p>
    );
  }

  return (
    <div className="space-y-2">
      {datasets.map((d) => (
        <div
          key={d.name}
          className="flex items-center justify-between rounded-lg border border-border bg-surface-active/30 px-3 py-2.5"
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <Database className="h-4 w-4 shrink-0 text-text-muted" />
            <span className="truncate text-sm font-medium text-text-primary">
              {d.name}
            </span>
          </div>
          <div className="flex items-center gap-4 shrink-0 ml-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-text-primary">
                {d.usage_count}
              </p>
              <p className="text-[10px] text-text-muted">uses</p>
            </div>
            {d.diversity_metric != null && (
              <div className="text-right">
                <p className="text-sm font-semibold text-text-primary">
                  {d.diversity_metric.toFixed(2)}
                </p>
                <p className="text-[10px] text-text-muted">diversity</p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
