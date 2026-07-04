import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui";

export interface SidebarSectionProps {
  label: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function SidebarSection({ label, children, defaultOpen = true }: SidebarSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const collapsed = useUIStore((s) => s.sidebarCollapsed);

  if (collapsed) {
    return <div className="space-y-0.5">{children}</div>;
  }

  return (
    <div className="space-y-0.5">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-3 py-1.5 text-xs font-medium text-text-muted transition-colors hover:text-text-secondary"
      >
        <ChevronDown
          className={cn("h-3 w-3 transition-transform", !open && "-rotate-90")}
        />
        {label}
      </button>
      {open && <div className="space-y-0.5">{children}</div>}
    </div>
  );
}
