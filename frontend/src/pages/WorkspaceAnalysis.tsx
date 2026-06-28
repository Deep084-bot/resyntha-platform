import { BarChart3 } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";

export function WorkspaceAnalysisPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Analysis"
        description="Compare papers and identify research trends"
      />

      <div className="rounded-lg border border-dashed border-border">
        <EmptyState
          icon={BarChart3}
          title="No analysis available"
          description="Collect papers and run extraction to enable comparison and trend analysis"
        />
      </div>
    </div>
  );
}
