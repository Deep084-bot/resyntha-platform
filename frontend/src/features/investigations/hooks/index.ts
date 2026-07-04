import type { Investigation, InvestigationStatus } from "@/types";

export type SortOption = "newest" | "oldest" | "alphabetical";

export interface FilterState {
  status: InvestigationStatus | "all";
  sort: SortOption;
  search: string;
}

const IN_PROGRESS: InvestigationStatus[] = [
  "created",
  "planning",
  "retrieving",
  "validating",
  "extracting",
  "analyzing",
  "generating",
];

export interface DashboardStats {
  total: number;
  running: number;
  completed: number;
  failed: number;
}

export function computeStats(
  investigations: Investigation[],
): DashboardStats {
  let running = 0;
  let completed = 0;
  let failed = 0;

  for (const inv of investigations) {
    if (inv.status === "completed") completed++;
    else if (inv.status === "failed") failed++;
    else if (IN_PROGRESS.includes(inv.status)) running++;
  }

  return {
    total: investigations.length,
    running,
    completed,
    failed,
  };
}

export function filterInvestigations(
  investigations: Investigation[],
  filters: FilterState,
): Investigation[] {
  let result = investigations;

  // Status filter
  if (filters.status !== "all") {
    result = result.filter((inv) => inv.status === filters.status);
  }

  // Search
  if (filters.search.trim()) {
    const q = filters.search.toLowerCase();
    result = result.filter(
      (inv) =>
        inv.title.toLowerCase().includes(q) ||
        inv.topic.toLowerCase().includes(q),
    );
  }

  // Sort
  result = [...result].sort((a, b) => {
    switch (filters.sort) {
      case "oldest":
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case "alphabetical":
        return a.title.localeCompare(b.title);
      case "newest":
      default:
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
  });

  return result;
}
