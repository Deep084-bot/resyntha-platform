import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface SectionCardProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}

export function SectionCard({
  title,
  icon,
  children,
  className,
  action,
}: SectionCardProps) {
  return (
    <section
      className={cn(
        "rounded-lg border border-border bg-card shadow-sm",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-text-primary">
          {icon && <span className="text-text-muted">{icon}</span>}
          {title}
        </h2>
        {action && <div>{action}</div>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}
