import { RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { PaperFiltersState } from "../hooks/usePaperFilters";

export interface PaperFiltersProps {
  filters: PaperFiltersState;
  sourceProviders: string[];
  yearRange: { min: number | null; max: number | null };
  activeFilterCount: number;
  onYearMinChange: (value: number | null) => void;
  onYearMaxChange: (value: number | null) => void;
  onSourceChange: (value: string) => void;
  onMinCitationsChange: (value: number | null) => void;
  onHasPdfChange: (value: boolean) => void;
  onHasDoiChange: (value: boolean) => void;
  onReset: () => void;
  className?: string;
}

export function PaperFilters({
  filters,
  sourceProviders,
  yearRange,
  activeFilterCount,
  onYearMinChange,
  onYearMaxChange,
  onSourceChange,
  onMinCitationsChange,
  onHasPdfChange,
  onHasDoiChange,
  onReset,
  className,
}: PaperFiltersProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
          Filters
          {activeFilterCount > 0 && (
            <span className="ml-1.5 rounded-full bg-accent-default px-1.5 py-0.5 text-[10px] text-white">
              {activeFilterCount}
            </span>
          )}
        </h3>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="h-6 px-2 text-xs"
            aria-label="Reset all filters"
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </Button>
        )}
      </div>

      {/* Year range */}
      <div>
        <label className="text-xs text-text-muted">Year</label>
        <div className="mt-1 flex items-center gap-2">
          <input
            type="number"
            value={filters.yearMin ?? ""}
            onChange={(e) =>
              onYearMinChange(e.target.value ? Number(e.target.value) : null)
            }
            placeholder={yearRange.min?.toString() ?? "Any"}
            aria-label="Minimum year"
            className="h-8 w-full rounded border border-input bg-transparent px-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <span className="text-text-muted text-xs">to</span>
          <input
            type="number"
            value={filters.yearMax ?? ""}
            onChange={(e) =>
              onYearMaxChange(e.target.value ? Number(e.target.value) : null)
            }
            placeholder={yearRange.max?.toString() ?? "Any"}
            aria-label="Maximum year"
            className="h-8 w-full rounded border border-input bg-transparent px-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* Source provider */}
      {sourceProviders.length > 0 && (
        <div>
          <label className="text-xs text-text-muted">Source</label>
          <select
            value={filters.sourceProvider}
            onChange={(e) => onSourceChange(e.target.value)}
            aria-label="Filter by source provider"
            className="mt-1 h-8 w-full rounded border border-input bg-transparent px-2 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All sources</option>
            {sourceProviders.map((s) => (
              <option key={s} value={s} className="capitalize">
                {s}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Minimum citations */}
      <div>
        <label className="text-xs text-text-muted">Min. Citations</label>
        <input
          type="number"
          value={filters.minCitations ?? ""}
          onChange={(e) =>
            onMinCitationsChange(
              e.target.value ? Number(e.target.value) : null,
            )
          }
          placeholder="0"
          aria-label="Minimum citation count"
          min={0}
          className="mt-1 h-8 w-full rounded border border-input bg-transparent px-2 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Checkboxes */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.hasPdf}
            onChange={(e) => onHasPdfChange(e.target.checked)}
            aria-label="Only show papers with PDF available"
            className="rounded border-input text-accent-default focus:ring-ring"
          />
          <span className="text-xs text-text-primary">Has PDF</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.hasDoi}
            onChange={(e) => onHasDoiChange(e.target.checked)}
            aria-label="Only show papers with DOI"
            className="rounded border-input text-accent-default focus:ring-ring"
          />
          <span className="text-xs text-text-primary">Has DOI</span>
        </label>
      </div>
    </div>
  );
}
