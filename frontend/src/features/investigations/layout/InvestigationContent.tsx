import { cn } from "@/lib/utils";

export interface InvestigationContentProps {
  children: React.ReactNode;
  className?: string;
}

export function InvestigationContent({
  children,
  className,
}: InvestigationContentProps) {
  return (
    <div className={cn("space-y-6", className)}>
      {children}
    </div>
  );
}
