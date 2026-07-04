import { cn } from "@/lib/utils";
import type { InvestigationStatus } from "@/types";

import type { FilterState, SortOption } from "../hooks";

const STATUS_OPTIONS: { value: InvestigationStatus | "all"; label: string }[] =
  [
    { value: "all", label: "All Statuses" },
    { value: "created", label: "Created" },
    { value: "planning", label: "Planning" },
    { value: "retrieving", label: "Retrieving" },
    { value: "validating", label: "Validating" },
    { value: "extracting", label: "Extracting" },
    { value: "analyzing", label: "Analyzing" },
    { value: "generating", label: "Generating" },
    { value: "completed", label: "Completed" },
    { value: "failed", label: "Failed" },
    { value: "cancelled", label: "Cancelled" },
  ];

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
  { value: "alphabetical", label: "Alphabetical" },
];

export interface InvestigationFiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  className?: string;
}

export function InvestigationFilters({
  filters,
  onChange,
  className,
}: InvestigationFiltersProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="flex items-center gap-2">
        <label htmlFor="status-filter" className="text-xs text-text-muted sr-only">
          Status
        </label>
        <select
          id="status-filter"
          value={filters.status}
          onChange={(e) =>
            onChange({
              ...filters,
              status: e.target.value as InvestigationStatus | "all",
            })
          }
          aria-label="Filter by status"
          className="rounded-md border border-input bg-surface-card px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="sort-filter" className="text-xs text-text-muted sr-only">
          Sort
        </label>
        <select
          id="sort-filter"
          value={filters.sort}
          onChange={(e) =>
            onChange({
              ...filters,
              sort: e.target.value as SortOption,
            })
          }
          aria-label="Sort order"
          className="rounded-md border border-input bg-surface-card px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
