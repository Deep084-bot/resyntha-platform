import { Skeleton } from "@/components/ui/skeleton";

export function ArtifactSkeleton() {
  return (
    <div className="space-y-6">
      {/* List skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-3 w-16" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>

      {/* Preview skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-48 w-full rounded-lg" />
      </div>

      {/* Metadata skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-3 w-12" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-48" />
        ))}
      </div>
    </div>
  );
}
