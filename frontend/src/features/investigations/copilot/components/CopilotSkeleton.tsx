import { Skeleton } from "@/components/ui/skeleton";

export function CopilotSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-7 w-56" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>
      <div className="space-y-3 rounded-2xl border border-border bg-surface p-4">
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-16 w-4/5 rounded-xl" />
        <Skeleton className="h-10 w-2/3 rounded-xl" />
      </div>
      <Skeleton className="h-24 w-full rounded-2xl" />
    </div>
  );
}