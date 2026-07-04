import { cn } from "@/lib/utils";

export interface SidebarFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function SidebarFooter({ children, className }: SidebarFooterProps) {
  return (
    <div className={cn("border-t border-border px-3 py-3 space-y-0.5", className)}>
      {children}
    </div>
  );
}
