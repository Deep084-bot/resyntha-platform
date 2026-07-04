import { cn } from "@/lib/utils";

import type { DashboardStats } from "../hooks";

const statCards: {
  key: keyof DashboardStats;
  label: string;
  color: string;
}[] = [
  { key: "total", label: "Total Investigations", color: "text-text-primary" },
  { key: "running", label: "Running", color: "text-accent-default" },
  { key: "completed", label: "Completed", color: "text-success" },
  { key: "failed", label: "Failed", color: "text-destructive" },
];

export interface QuickStatsProps {
  stats: DashboardStats;
  className?: string;
}

export function QuickStats({ stats, className }: QuickStatsProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-2 gap-4 md:grid-cols-4",
        className,
      )}
    >
      {statCards.map((card) => (
        <div
          key={card.key}
          className="rounded-lg border border-border bg-surface-card p-4"
        >
          <p className="text-xs text-text-muted">{card.label}</p>
          <p
            className={cn(
              "mt-1 text-2xl font-semibold tabular-nums",
              card.color,
            )}
          >
            {stats[card.key]}
          </p>
        </div>
      ))}
    </div>
  );
}
