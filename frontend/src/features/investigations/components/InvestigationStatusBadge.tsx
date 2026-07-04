import { StatusBadge } from "@/components/ui/status-badge";
import type { InvestigationStatus } from "@/types";
import { mapInvestigationStatus } from "@/types";

export interface InvestigationStatusBadgeProps {
  status: InvestigationStatus;
  className?: string;
}

export function InvestigationStatusBadge({
  status,
  className,
}: InvestigationStatusBadgeProps) {
  return (
    <StatusBadge
      status={mapInvestigationStatus(status)}
      label={status}
      className={className}
    />
  );
}
