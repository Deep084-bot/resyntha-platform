import { Fragment } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";

import { useBreadcrumbStore } from "@/stores/breadcrumbs";
import { cn } from "@/lib/utils";

export interface BreadcrumbsProps {
  className?: string;
}

const SEGMENT_LABELS: Record<string, string> = {
  investigations: "Investigations",
  pipeline: "Pipeline",
  settings: "Settings",
  research: "Research",
};

export function Breadcrumbs({ className }: BreadcrumbsProps) {
  const { pathname } = useLocation();
  const overrides = useBreadcrumbStore((s) => s.labels);
  const segments = pathname.split("/").filter(Boolean);

  return (
    <nav
      className={cn("flex items-center gap-1.5 text-xs text-text-muted", className)}
      aria-label="Breadcrumb"
    >
      <Link to="/" className="transition-colors hover:text-text-secondary">
        Home
      </Link>
      {segments.map((segment, i) => {
        const href = "/" + segments.slice(0, i + 1).join("/");
        const label =
          overrides[segment] ??
          SEGMENT_LABELS[segment] ??
          (segment.charAt(0).toUpperCase() + segment.slice(1));
        const isLast = i === segments.length - 1;

        return (
          <Fragment key={href}>
            <ChevronRight className="h-3 w-3 shrink-0" aria-hidden="true" />
            {isLast ? (
              <span className="max-w-[200px] truncate text-text-primary" aria-current="page">
                {label}
              </span>
            ) : (
              <Link
                to={href}
                className="max-w-[200px] truncate transition-colors hover:text-text-secondary"
              >
                {label}
              </Link>
            )}
          </Fragment>
        );
      })}
    </nav>
  );
}
