import { useParams } from "react-router-dom";

import { Skeleton } from "@/components/ui/skeleton";
import { TimelineItem } from "@/components/ui/timeline-item";
import { useTimeline } from "@/hooks/useInvestigations";
import { mapTimelineStatus } from "@/types";

export function WorkspaceTimelinePage() {
  const { id } = useParams();
  const { data: events, isLoading, isError } = useTimeline(id);

  if (isLoading) {
    return (
      <div className="max-w-2xl space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="h-4 w-4 rounded-full shrink-0" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-72" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        Failed to load timeline events.
      </p>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-md border border-dashed border-border">
        <p className="text-sm text-text-muted">
          No timeline events yet. Create an investigation to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      {events.map((event, i) => (
        <TimelineItem
          key={`${event.created_at}-${i}`}
          stage={event.stage}
          status={mapTimelineStatus(event.status)}
          message={event.message}
          timestamp={new Date(event.created_at).toLocaleString()}
          isLast={i === events.length - 1}
        />
      ))}
    </div>
  );
}
