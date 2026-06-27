import { BookOpen } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";

export function WorkspacePapersPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Papers"
        description="Retrieved papers attached to this investigation"
      />

      <div className="rounded-lg border border-dashed border-border">
        <EmptyState
          icon={BookOpen}
          title="No papers collected"
          description="Run the retrieval pipeline to search for papers"
        />
      </div>
    </div>
  );
}
