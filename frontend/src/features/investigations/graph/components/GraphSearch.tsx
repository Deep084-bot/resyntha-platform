import { Search, X } from "lucide-react";

interface GraphSearchProps {
  value: string;
  onChange: (value: string) => void;
}

export function GraphSearch({ value, onChange }: GraphSearchProps) {
  return (
    <div className="relative">
      <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search nodes..."
        className="w-56 rounded-md border border-border bg-card py-1.5 pl-8 pr-8 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-default"
        aria-label="Search graph nodes"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
          aria-label="Clear search"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
