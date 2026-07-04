import {
  BarChart3,
  FlaskConical,
  Cpu,
  Database,
} from "lucide-react";

import type { TemporalTrend } from "../types";

export interface TemporalTimelineProps {
  trends: TemporalTrend[];
}

const METRICS: {
  key: keyof Omit<TemporalTrend, "year">;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { key: "paper_count", label: "Papers", icon: BarChart3 },
  { key: "methodology_adoptions", label: "Methodologies", icon: FlaskConical },
  { key: "technology_adoptions", label: "Technologies", icon: Cpu },
  { key: "dataset_usage_count", label: "Datasets", icon: Database },
];

export function TemporalTimeline({ trends }: TemporalTimelineProps) {
  if (trends.length === 0) {
    return (
      <p className="text-sm text-text-muted">No temporal data available.</p>
    );
  }

  const maxPaperCount = Math.max(...trends.map((t) => t.paper_count), 1);

  return (
    <div className="space-y-4">
      {trends.map((trend) => {
        const barWidth = Math.max(
          4,
          (trend.paper_count / maxPaperCount) * 100,
        );

        return (
          <div key={trend.year} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-text-primary">
                {trend.year}
              </span>
              <span className="text-xs text-text-muted">
                {trend.paper_count} papers
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-surface-active">
              <div
                className="h-2 rounded-full bg-accent-default transition-all"
                style={{ width: `${barWidth}%` }}
                role="progressbar"
                aria-valuenow={trend.paper_count}
                aria-valuemin={0}
                aria-valuemax={maxPaperCount}
                aria-label={`${trend.paper_count} papers in ${trend.year}`}
              />
            </div>
            <div className="flex flex-wrap gap-3 text-xs text-text-muted">
              {METRICS.map(({ key, label, icon: Icon }) => {
                const val = trend[key] as number;
                if (val === 0) return null;
                return (
                  <span key={key} className="flex items-center gap-1">
                    <Icon className="h-3 w-3" />
                    {val} {label.toLowerCase()}
                  </span>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
