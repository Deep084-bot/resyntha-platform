import { Lightbulb } from "lucide-react";

import type { Observation } from "../types";

export interface ObservationCardProps {
  observation: Observation;
}

export function ObservationCard({ observation }: ObservationCardProps) {
  return (
    <div className="rounded-lg border border-accent-default/20 bg-accent-default/5 px-4 py-3">
      <div className="flex items-start gap-3">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-accent-default" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded bg-accent-default/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-accent-default">
              {observation.category}
            </span>
          </div>
          <p className="mt-1 text-sm font-medium text-text-primary">
            {observation.label}
          </p>
          <p className="mt-0.5 text-sm text-text-secondary">
            {observation.value}
          </p>
        </div>
      </div>
    </div>
  );
}
