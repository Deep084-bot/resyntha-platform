import { NavLink } from "react-router-dom";
import { type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui";

export interface SidebarItemProps {
  icon: LucideIcon;
  label: string;
  to: string;
  end?: boolean;
}

export function SidebarItem({ icon: Icon, label, to, end }: SidebarItemProps) {
  const collapsed = useUIStore((s) => s.sidebarCollapsed);

  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-sidebar-active text-sidebar-text-active"
            : "text-sidebar-text hover:bg-sidebar-hover hover:text-sidebar-text-active",
          collapsed && "justify-center px-2",
        )
      }
      title={collapsed ? label : undefined}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
}
