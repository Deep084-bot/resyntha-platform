import { cn } from "@/lib/utils";

export interface WorkspaceProps {
  children: React.ReactNode;
  className?: string;
}

export function Workspace({ children, className }: WorkspaceProps) {
  return (
    <div className={cn("flex h-full flex-col", className)}>
      {children}
    </div>
  );
}
