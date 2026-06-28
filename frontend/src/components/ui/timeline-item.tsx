import { cn } from "@/lib/utils";
import { StatusBadge, type StatusVariant } from "@/components/ui/status-badge";

interface TimelineItemProps {
  stage: string;
  status: StatusVariant;
  message: string;
  timestamp?: string;
  isLast?: boolean;
}

export function TimelineItem({
  stage,
  status,
  message,
  timestamp,
  isLast = false,
}: TimelineItemProps) {
  return (
    <div className="relative flex gap-4 pb-1">
      {/* Vertical line */}
      {!isLast && (
        <div className="absolute left-[7px] top-4 h-full w-px bg-border" />
      )}

      {/* Dot */}
      <div className="relative mt-1.5 shrink-0">
        <div
          className={cn(
            "h-3.5 w-3.5 rounded-full border-2",
            status === "success" && "border-success",
            status === "failure" && "border-destructive",
            status === "running" && "border-accent-default",
            status === "pending" && "border-warning",
            status === "skipped" && "border-text-muted",
            "bg-surface-base",
          )}
        />
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary capitalize">
            {stage}
          </span>
          <StatusBadge status={status} />
        </div>
        <p className="mt-0.5 text-sm text-text-secondary">{message}</p>
        {timestamp && (
          <p className="mt-0.5 text-xs text-text-muted">{timestamp}</p>
        )}
      </div>
    </div>
  );
}
