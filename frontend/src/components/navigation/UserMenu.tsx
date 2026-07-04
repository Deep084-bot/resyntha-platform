import { LogOut, User } from "lucide-react";

import { cn } from "@/lib/utils";

export interface UserMenuProps {
  className?: string;
}

export function UserMenu({ className }: UserMenuProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <button
        type="button"
        className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text-primary"
        aria-label="User menu"
      >
        <User className="h-4 w-4" />
        <span className="hidden md:inline">User</span>
      </button>
      <button
        type="button"
        className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text-primary"
        aria-label="Sign out"
      >
        <LogOut className="h-4 w-4" />
      </button>
    </div>
  );
}
