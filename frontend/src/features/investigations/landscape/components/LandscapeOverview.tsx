import { BookOpen, Building2, Cpu, Database, FlaskConical, Users } from "lucide-react";

import type { LandscapeOverview as OverviewData } from "../types";

export interface LandscapeOverviewProps {
  data: OverviewData;
}

const METRICS: {
  key: keyof OverviewData;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { key: "total_papers", label: "Papers", icon: BookOpen },
  { key: "total_authors", label: "Authors", icon: Users },
  { key: "total_institutions", label: "Institutions", icon: Building2 },
  { key: "total_technologies", label: "Technologies", icon: Cpu },
  { key: "total_datasets", label: "Datasets", icon: Database },
  { key: "total_methodologies", label: "Methodologies", icon: FlaskConical },
];

export function LandscapeOverview({ data }: LandscapeOverviewProps) {
  return (
    <div>
      <p className="mb-4 text-sm text-text-muted">
        Analysis covering <strong>{data.years_covered}</strong>
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {METRICS.map(({ key, label, icon: Icon }) => (
          <div
            key={key}
            className="flex flex-col items-center gap-1 rounded-lg border border-border bg-surface-active/50 px-3 py-3 text-center"
          >
            <Icon className="h-4 w-4 text-text-muted" />
            <span className="text-xl font-bold text-text-primary">
              {data[key] as number}
            </span>
            <span className="text-xs text-text-muted">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
