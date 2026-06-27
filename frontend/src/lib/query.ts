import { QueryClient } from "@tanstack/react-query";

/**
 * Singleton QueryClient with sensible defaults.
 * Stale times are kept high because research data changes infrequently.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});
