import { type ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "@/stores/auth";

interface RequireAuthProps {
  children: ReactNode;
  fallback?: string;
}

export function RequireAuth({ children, fallback = "/" }: RequireAuthProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  if (!isAuthenticated) {
    return <Navigate to={fallback} replace />;
  }
  return <>{children}</>;
}

export function RequireAnonymous({ children, fallback = "/" }: RequireAuthProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  if (isAuthenticated) {
    return <Navigate to={fallback} replace />;
  }
  return <>{children}</>;
}
