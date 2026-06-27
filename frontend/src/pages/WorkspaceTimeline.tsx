import { TimelineItem } from "@/components/ui/timeline-item";

const events = [
  { stage: "created", status: "success" as const, message: "Investigation created", timestamp: "2026-06-27 10:00 UTC" },
  { stage: "retrieving", status: "running" as const, message: "Paper retrieval started", timestamp: "2026-06-27 10:05 UTC" },
  { stage: "extracting", status: "pending" as const, message: "Awaiting retrieval completion" },
];

export function WorkspaceTimelinePage() {
  return (
    <div className="max-w-2xl">
      {events.map((event, i) => (
        <TimelineItem
          key={event.stage}
          stage={event.stage}
          status={event.status}
          message={event.message}
          timestamp={event.timestamp}
          isLast={i === events.length - 1}
        />
      ))}
    </div>
  );
}
