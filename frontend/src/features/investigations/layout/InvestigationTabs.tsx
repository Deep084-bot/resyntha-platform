import { useCallback, useEffect, useRef } from "react";
import { Lock, type LucideIcon } from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";

import { cn } from "@/lib/utils";

export interface TabDefinition {
  label: string;
  to: string;
  disabled?: boolean;
  tooltip?: string;
  icon?: LucideIcon;
}

export interface InvestigationTabsProps {
  tabs: TabDefinition[];
  className?: string;
}

export function InvestigationTabs({ tabs, className }: InvestigationTabsProps) {
  const { id } = useParams();
  const location = useLocation();
  const tabListRef = useRef<HTMLDivElement>(null);

  const activeIndex = tabs.findIndex((tab) => {
    const fullPath = tab.to
      ? `/investigations/${id}/${tab.to}`
      : `/investigations/${id}`;
    return (
      location.pathname === fullPath ||
      (tab.to === "" && location.pathname === `/investigations/${id}`)
    );
  });

  const enabledIndices = tabs
    .map((tab, index) => (tab.disabled ? null : index))
    .filter((index): index is number => index !== null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const tabElements = tabListRef.current?.querySelectorAll<HTMLElement>(
        '[role="tab"]:not([aria-disabled="true"])',
      );
      if (!tabElements || tabElements.length === 0) return;

      let newIndex: number | null = null;
      const activeEnabledIndex = enabledIndices.indexOf(activeIndex);

      switch (e.key) {
        case "ArrowRight":
          newIndex =
            enabledIndices[(activeEnabledIndex + 1) % enabledIndices.length] ??
            null;
          break;
        case "ArrowLeft":
          newIndex =
            enabledIndices[
              (activeEnabledIndex - 1 + enabledIndices.length) %
                enabledIndices.length
            ] ?? null;
          break;
        case "Home":
          newIndex = enabledIndices[0] ?? null;
          break;
        case "End":
          newIndex = enabledIndices[enabledIndices.length - 1] ?? null;
          break;
      }

      if (newIndex !== null) {
        e.preventDefault();
        tabElements[newIndex]?.click();
        tabElements[newIndex]?.focus();
      }
    },
    [activeIndex, enabledIndices],
  );

  useEffect(() => {
    const el = tabListRef.current;
    if (!el) return;
    el.addEventListener("keydown", handleKeyDown);
    return () => el.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      ref={tabListRef}
      role="tablist"
      aria-label="Investigation sections"
      className={cn("flex gap-0 overflow-x-auto", className)}
    >
      {tabs.map((tab, i) => {
        const href = tab.to
          ? `/investigations/${id}/${tab.to}`
          : `/investigations/${id}`;
        const isActive = i === activeIndex;
        const Icon = tab.disabled ? Lock : tab.icon;

        if (tab.disabled) {
          return (
            <button
              key={tab.label}
              type="button"
              role="tab"
              aria-selected={false}
              aria-disabled="true"
              tabIndex={-1}
              title={tab.tooltip}
              className={cn(
                "inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors",
                "cursor-not-allowed text-text-muted",
              )}
            >
              <Lock className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{tab.label}</span>
            </button>
          );
        }

        return (
          <Link
            key={tab.label}
            to={href}
            role="tab"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.label.toLowerCase()}`}
            tabIndex={isActive ? 0 : -1}
            replace
            className={cn(
              "relative inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
              isActive
                ? "text-text-primary"
                : "text-text-muted hover:text-text-secondary",
            )}
          >
            {Icon && <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
            {tab.label}
            {isActive && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-accent-default" />
            )}
          </Link>
        );
      })}
    </div>
  );
}
