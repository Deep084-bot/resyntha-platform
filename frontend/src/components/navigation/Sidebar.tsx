import { PanelLeft, PanelLeftClose, X } from "lucide-react";

import { useUIStore } from "@/stores/ui";
import { cn } from "@/lib/utils";

export interface SidebarProps {
  children?: React.ReactNode;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

function LightningLogo({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      width="48"
      height="46"
      fill="none"
      viewBox="0 0 48 46"
    >
      <path
        fill="#863bff"
        d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z"
      />
    </svg>
  );
}

export function Sidebar({ children, mobileOpen, onMobileClose }: SidebarProps) {
  const collapsed = useUIStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);

  return (
    <>
      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          // Desktop: relative (part of flow), always visible
          "hidden lg:flex lg:flex-col lg:h-full",
          "border-r border-border bg-sidebar-base",
          "transition-all duration-200 flex-shrink-0",
          collapsed ? "lg:w-16" : "lg:w-56",
        )}
      >
        <InnerSidebar collapsed={collapsed} onToggle={toggleSidebar}>
          {children}
        </InnerSidebar>
      </aside>

      {/* Mobile overlay sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col",
          "border-r border-border bg-sidebar-base",
          "transition-transform duration-200 ease-in-out w-56",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "lg:hidden",
        )}
      >
        <InnerSidebar
          collapsed={false}
          onToggle={onMobileClose}
          closeIcon
        >
          {children}
        </InnerSidebar>
      </aside>
    </>
  );
}

/* ── Inner shared sidebar content ────────────────────────────── */

interface InnerSidebarProps {
  children: React.ReactNode;
  collapsed: boolean;
  onToggle?: () => void;
  closeIcon?: boolean;
}

function InnerSidebar({ children, collapsed, onToggle, closeIcon }: InnerSidebarProps) {
  return (
    <>
      {/* Brand */}
      <div className="flex h-14 items-center gap-2.5 px-5 shrink-0">
        <LightningLogo className="h-7 w-7 shrink-0" />
        {!collapsed && (
          <span className="text-sm font-semibold text-text-primary">
            Resyntha
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {children}
      </nav>

      {/* Toggle / close */}
      <div className="border-t border-border px-3 py-3 shrink-0">
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center justify-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-sidebar-text transition-colors hover:bg-sidebar-hover hover:text-sidebar-text-active"
          aria-label={
            closeIcon
              ? "Close navigation"
              : collapsed
                ? "Expand sidebar"
                : "Collapse sidebar"
          }
        >
          {closeIcon ? (
            <X className="h-4 w-4" />
          ) : collapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
          {!collapsed && !closeIcon && <span>Collapse</span>}
        </button>
      </div>
    </>
  );
}
