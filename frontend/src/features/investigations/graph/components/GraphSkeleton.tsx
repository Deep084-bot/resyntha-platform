import { Skeleton } from "@/components/ui/skeleton";

export function GraphSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading graph">
      <div className="flex gap-2">
        <Skeleton className="h-7 w-20 rounded-md" />
        <Skeleton className="h-7 w-20 rounded-md" />
        <Skeleton className="h-7 w-20 rounded-md" />
      </div>
      <div className="relative h-[400px] rounded-md border border-border bg-card">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="space-y-3">
            <div className="flex gap-4">
              <Skeleton className="h-16 w-36 rounded-lg" />
              <Skeleton className="h-16 w-36 rounded-lg" />
              <Skeleton className="h-16 w-36 rounded-lg" />
            </div>
            <div className="flex justify-center gap-4">
              <Skeleton className="h-16 w-36 rounded-lg" />
              <Skeleton className="h-16 w-36 rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
