import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import { queryClient } from "@/lib/query";
import { router } from "@/routes";

/**
 * Root application component.
 *
 * Wires together:
 * - TanStack Query for server-state management
 * - React Router for client-side navigation
 */
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
