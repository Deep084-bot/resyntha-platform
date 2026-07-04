import { ArrowDownAZ, BarChart3, Calendar } from "lucide-react";

import { cn } from "@/lib/utils";
import type { SortField } from "../hooks/usePaperFilters";

export interface PaperSortProps {
  value: SortField;
  onChange: (value: SortField) => void;
  className?: string;
}

const SORT_OPTIONS: { value: SortField; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: "newest", label: "Newest", icon: Calendar },
  { value: "oldest", label: "Oldest", icon: Calendar },
  { value: "most-cited", label: "Most cited", icon: BarChart3 },
  { value: "alphabetical", label: "A\u2013Z", icon: ArrowDownAZ },
];

export function PaperSort({ value, onChange, className }: PaperSortProps) {
  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <span className="text-xs text-text-muted whitespace-nowrap">Sort by</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as SortField)}
        aria-label="Sort papers"
        className="h-8 rounded border border-input bg-transparent px-2 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {SORT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
