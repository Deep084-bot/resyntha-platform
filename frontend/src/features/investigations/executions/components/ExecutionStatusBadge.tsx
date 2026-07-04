import type { ExecutionStatus as ExecStatus } from "@/types";
import { mapExecutionStatus } from "@/types";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

export interface ExecutionStatusBadgeProps {
  status: ExecStatus;
  className?: string;
}

const labelMap: Record<ExecStatus, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export function ExecutionStatusBadge({
  status,
  className,
}: ExecutionStatusBadgeProps) {
  return (
    <StatusBadge
      status={mapExecutionStatus(status)}
      label={labelMap[status]}
      className={cn("capitalize", className)}
    />
  );
}
