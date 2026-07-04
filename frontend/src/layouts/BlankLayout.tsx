import { Outlet } from "react-router-dom";

import { cn } from "@/lib/utils";

export interface BlankLayoutProps {
  className?: string;
}

export function BlankLayout({ className }: BlankLayoutProps) {
  return (
    <div
      className={cn(
        "flex min-h-screen items-center justify-center bg-surface-base",
        className,
      )}
    >
      <Outlet />
    </div>
  );
}
