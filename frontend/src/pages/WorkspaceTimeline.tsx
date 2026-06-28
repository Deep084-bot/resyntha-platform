import { useParams } from "react-router-dom";

import { Skeleton } from "@/components/ui/skeleton";
import { TimelineItem } from "@/components/ui/timeline-item";
import { useTimeline } from "@/hooks/useInvestigations";
import { formatDate, formatElapsed } from "@/lib/format";
import { mapTimelineStatus, type TimelineEvent } from "@/types";

function groupByDate(events: TimelineEvent[]): Record<string, TimelineEvent[]> {
  const groups: Record<string, TimelineEvent[]> = {};
  for (const event of events) {
    const date = formatDate(event.created_at);
    if (!groups[date]) groups[date] = [];
    groups[date].push(event);
  }
  return groups;
}

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
          No timeline events yet. Run the retrieval pipeline to get started.
        </p>
      </div>
    );
  }

  const reversed = [...events].reverse();
  const grouped = groupByDate(reversed);
  const sortedDates = Object.keys(grouped).sort(
    (a, b) => new Date(b).getTime() - new Date(a).getTime(),
  );

  return (
    <div className="max-w-2xl">
      {sortedDates.map((date) => {
        const entries = grouped[date];
        if (!entries) return null;
        return (
          <div key={date} className="mb-6">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                {date}
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <div className="space-y-1">
              {entries.map((event, i) => (
                <TimelineItem
                  key={`${event.created_at}-${i}`}
                  stage={event.stage}
                  status={mapTimelineStatus(event.status)}
                  message={event.message}
                  timestamp={formatElapsed(event.created_at)}
                  isLast={i === entries.length - 1}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
