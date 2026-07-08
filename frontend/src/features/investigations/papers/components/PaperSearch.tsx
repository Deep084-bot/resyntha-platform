import { Search, X } from "lucide-react";

import { cn } from "@/lib/utils";

export interface PaperSearchProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function PaperSearch({
  value,
  onChange,
  placeholder = "Search titles, authors, abstracts…",
  className,
}: PaperSearchProps) {
  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        role="searchbox"
        aria-label="Search papers"
        className={cn(
          "h-9 w-full rounded-md border border-input bg-transparent pl-9 pr-8 text-sm text-text-primary",
          "placeholder:text-text-muted",
          "focus:outline-none focus:ring-2 focus:ring-ring",
          "transition-colors",
        )}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-text-muted hover:text-text-primary"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
