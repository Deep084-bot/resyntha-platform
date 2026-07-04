import { cn } from "@/lib/utils";

export interface WorkspaceHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function WorkspaceHeader({ children, className }: WorkspaceHeaderProps) {
  return (
    <div className={cn("border-b border-border", className)}>
      <div className="px-6 pt-4 pb-0">
        {children}
      </div>
    </div>
  );
}
