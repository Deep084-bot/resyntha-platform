import { Activity, FileText, Search, Users } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const stats = [
  { label: "Papers Retrieved", value: "24", icon: Search },
  { label: "Artifacts Created", value: "3", icon: FileText },
  { label: "Pipeline Runs", value: "2", icon: Activity },
  { label: "Key Findings", value: "—", icon: Users },
];

export function WorkspaceOverviewPage() {
  return (
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-text-muted">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-text-muted" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-text-primary">
                {stat.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent timeline preview */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-32 items-center justify-center rounded-md border border-dashed border-border">
            <p className="text-sm text-text-muted">
              Timeline events will appear here
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Pipeline status */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-border">
            <p className="text-sm text-text-muted">
              Pipeline execution details will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
