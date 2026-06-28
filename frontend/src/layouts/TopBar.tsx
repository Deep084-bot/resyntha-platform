import { Search } from "lucide-react";

export function TopBar() {
  return (
    <header className="flex h-14 items-center gap-4 border-b border-border px-6">
      {/* Breadcrumb / page title area — pages will populate via outlet context */}
      <div className="flex-1" />

      {/* Global search (placeholder) */}
      <div className="relative hidden w-72 md:block">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="search"
          placeholder="Search investigations…"
          className="w-full rounded-md border border-input bg-surface-card py-1.5 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
    </header>
  );
}
