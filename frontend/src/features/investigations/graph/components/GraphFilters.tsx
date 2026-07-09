import { X } from "lucide-react";

import { cn } from "@/lib/utils";
import type { NodeType } from "../types/graph";

interface FilterState {
  nodeTypes: Set<NodeType>;
  searchQuery: string;
}

interface GraphFiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableTypes: NodeType[];
}

const FILTER_LABELS: Record<NodeType, string> = {
  paper: "Papers",
  author: "Authors",
  institution: "Institutions",
  dataset: "Datasets",
  technology: "Technologies",
  methodology: "Methodologies",
  research_domain: "Research Domains",
};

const FILTER_COLORS: Record<NodeType, string> = {
  paper: "bg-blue-500/10 text-blue-700 border-blue-300",
  author: "bg-emerald-500/10 text-emerald-700 border-emerald-300",
  institution: "bg-orange-500/10 text-orange-700 border-orange-300",
  dataset: "bg-purple-500/10 text-purple-700 border-purple-300",
  technology: "bg-cyan-500/10 text-cyan-700 border-cyan-300",
  methodology: "bg-pink-500/10 text-pink-700 border-pink-300",
  research_domain: "bg-amber-500/10 text-amber-700 border-amber-300",
};

export function GraphFilters({ filters, onChange, availableTypes }: GraphFiltersProps) {
  const allSelected = availableTypes.every((t) => filters.nodeTypes.has(t));

  const handleToggleAll = () => {
    if (allSelected) {
      onChange({ ...filters, nodeTypes: new Set() });
    } else {
      onChange({ ...filters, nodeTypes: new Set(availableTypes) });
    }
  };

  const handleToggle = (type: NodeType) => {
    const next = new Set(filters.nodeTypes);
    if (next.has(type)) {
      next.delete(type);
    } else {
      next.add(type);
    }
    onChange({ ...filters, nodeTypes: next });
  };

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Graph filters">
      <button
        type="button"
        onClick={handleToggleAll}
        className="rounded-md border border-border px-2.5 py-1 text-[11px] font-medium text-text-muted hover:bg-surface-hover transition-colors"
      >
        {allSelected ? "Clear All" : "Show All"}
      </button>

      {availableTypes.map((type) => {
        const isActive = filters.nodeTypes.has(type);
        return (
          <button
            key={type}
            type="button"
            onClick={() => handleToggle(type)}
            className={cn(
              "rounded-md border px-2.5 py-1 text-[11px] font-medium transition-colors",
              isActive
                ? FILTER_COLORS[type]
                : "border-border text-text-muted opacity-50",
            )}
            aria-pressed={isActive}
          >
            {FILTER_LABELS[type]}
            {!isActive && <X className="ml-1 inline-block h-2.5 w-2.5" />}
          </button>
        );
      })}
    </div>
  );
}
