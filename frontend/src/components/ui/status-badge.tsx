import { cn } from "@/lib/utils";

export type StatusVariant =
  | "success"
  | "failure"
  | "running"
  | "pending"
  | "skipped"
  | "default";

interface StatusBadgeProps {
  status: StatusVariant;
  label?: string;
  className?: string;
}

const colorMap: Record<StatusVariant, string> = {
  success: "bg-success/10 text-success",
  failure: "bg-destructive/10 text-destructive",
  running: "bg-accent-default/10 text-accent-default",
  pending: "bg-warning/10 text-warning",
  skipped: "bg-text-muted/10 text-text-muted",
  default: "bg-secondary text-secondary-foreground",
};

const dotMap: Record<StatusVariant, string> = {
  success: "bg-success",
  failure: "bg-destructive",
  running: "bg-accent-default",
  pending: "bg-warning",
  skipped: "bg-text-muted",
  default: "bg-text-muted",
};

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        colorMap[status],
        className,
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          dotMap[status],
        )}
      />
      {label ?? status}
    </span>
  );
}
