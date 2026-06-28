import { cn } from "@/lib/utils";
import { StatusBadge, type StatusVariant } from "@/components/ui/status-badge";

interface PipelineStageCardProps {
  name: string;
  description: string;
  status: StatusVariant;
  duration?: string;
  isActive?: boolean;
}

export function PipelineStageCard({
  name,
  description,
  status,
  duration,
  isActive = false,
}: PipelineStageCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border p-4 transition-colors",
        isActive
          ? "border-accent-default/40 bg-accent-default/5"
          : "border-border bg-surface-card",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-text-primary capitalize">
              {name}
            </p>
            {isActive && (
              <span className="h-2 w-2 rounded-full bg-accent-default animate-pulse" />
            )}
          </div>
          <p className="mt-0.5 text-xs text-text-muted">{description}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {duration && (
            <span className="text-xs text-text-muted">{duration}</span>
          )}
          <StatusBadge status={status} />
        </div>
      </div>
    </div>
  );
}
