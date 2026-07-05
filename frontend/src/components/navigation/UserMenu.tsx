import { cn } from "@/lib/utils";

export interface UserMenuProps {
  className?: string;
}

export function UserMenu({ className }: UserMenuProps) {
  // Authentication is not implemented in the backend.
  // Hiding user menu to avoid exposing non-functional controls.
  return (
    <div className={cn("flex items-center gap-2 text-xs text-text-muted", className)}>
      Developer Mode
    </div>
  );
}
