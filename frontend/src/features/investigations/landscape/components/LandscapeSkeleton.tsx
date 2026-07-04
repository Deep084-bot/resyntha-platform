import { Skeleton } from "@/components/ui/skeleton";

export function LandscapeSkeleton() {
  return (
    <div className="space-y-6" data-testid="landscape-skeleton">
      {/* Overview skeletons */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-5 py-3.5">
          <Skeleton className="h-5 w-32" />
        </div>
        <div className="px-5 py-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col items-center gap-2 px-3 py-3">
                <Skeleton className="h-4 w-4 rounded" />
                <Skeleton className="h-6 w-10" />
                <Skeleton className="h-3 w-14" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Section skeletons */}
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="rounded-lg border border-border bg-card shadow-sm"
        >
          <div className="border-b border-border px-5 py-3.5">
            <Skeleton className="h-5 w-40" />
          </div>
          <div className="px-5 py-4 space-y-2">
            {Array.from({ length: 3 }).map((_, j) => (
              <Skeleton key={j} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
