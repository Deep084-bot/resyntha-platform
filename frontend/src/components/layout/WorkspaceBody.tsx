import { cn } from "@/lib/utils";

export interface WorkspaceBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function WorkspaceBody({ children, className }: WorkspaceBodyProps) {
  return (
    <div className={cn("flex-1 overflow-y-auto p-6", className)}>
      {children}
    </div>
  );
}
