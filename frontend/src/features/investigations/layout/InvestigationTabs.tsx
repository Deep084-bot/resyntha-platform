import { useCallback, useEffect, useRef } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { cn } from "@/lib/utils";

export interface TabDefinition {
  label: string;
  to: string;
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

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const tabElements = tabListRef.current?.querySelectorAll<HTMLAnchorElement>(
        '[role="tab"]',
      );
      if (!tabElements || tabElements.length === 0) return;

      let newIndex: number | null = null;

      switch (e.key) {
        case "ArrowRight":
          newIndex = (activeIndex + 1) % tabs.length;
          break;
        case "ArrowLeft":
          newIndex = (activeIndex - 1 + tabs.length) % tabs.length;
          break;
        case "Home":
          newIndex = 0;
          break;
        case "End":
          newIndex = tabs.length - 1;
          break;
      }

      if (newIndex !== null) {
        e.preventDefault();
        tabElements[newIndex]?.click();
        tabElements[newIndex]?.focus();
      }
    },
    [activeIndex, tabs.length],
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
              "relative px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
              isActive
                ? "text-text-primary"
                : "text-text-muted hover:text-text-secondary",
            )}
          >
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
