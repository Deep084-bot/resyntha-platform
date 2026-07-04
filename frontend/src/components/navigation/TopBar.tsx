import { Menu, Search } from "lucide-react";

import { Breadcrumbs } from "./Breadcrumbs";
import { UserMenu } from "./UserMenu";
import { cn } from "@/lib/utils";

export interface TopBarProps {
  className?: string;
  onMenuToggle?: () => void;
}

export function TopBar({ className, onMenuToggle }: TopBarProps) {
  return (
    <header
      className={cn(
        "flex h-14 items-center gap-4 border-b border-border bg-surface-base px-4 lg:px-6",
        className,
      )}
    >
      {/* Mobile menu toggle */}
      <button
        type="button"
        onClick={onMenuToggle}
        className="flex items-center justify-center rounded-md p-1.5 text-text-muted transition-colors hover:text-text-primary lg:hidden"
        aria-label="Toggle navigation menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Breadcrumbs */}
      <Breadcrumbs className="flex-1" />

      {/* Search */}
      <div className="relative hidden w-72 md:block">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="search"
          placeholder="Search investigations\u2026"
          className="w-full rounded-md border border-input bg-surface-card py-1.5 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Right actions */}
      <UserMenu />
    </header>
  );
}
