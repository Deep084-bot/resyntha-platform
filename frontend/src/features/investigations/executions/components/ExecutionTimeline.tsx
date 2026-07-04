import type { ExecutionStage } from "@/types";

import { ExecutionStageCard } from "./ExecutionStageCard";

export interface ExecutionTimelineProps {
  stages: ExecutionStage[];
  className?: string;
}

export function ExecutionTimeline({
  stages,
  className,
}: ExecutionTimelineProps) {
  if (stages.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-md border border-dashed border-border">
        <p className="text-sm text-text-muted">No stages recorded.</p>
      </div>
    );
  }

  return (
    <div className={className} role="list" aria-label="Pipeline stages">
      {stages.map((stage, i) => (
        <div key={stage.id} role="listitem">
          <ExecutionStageCard
            stage={stage}
            isLast={i === stages.length - 1}
          />
        </div>
      ))}
    </div>
  );
}
