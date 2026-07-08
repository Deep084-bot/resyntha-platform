import { GitBranch, Users, Building2, Share2 } from "lucide-react";

import type {
  CollaborationData,
  CentralityEntry,
  CollaborationLink,
} from "../types";
export interface CollaborationListProps {
  data: CollaborationData;
}

function CollaborationLinkRow({
  link,
  icon: Icon,
}: {
  link: CollaborationLink;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-surface-active/30 px-3 py-2 text-sm">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Icon className="h-4 w-4 shrink-0 text-text-muted" />
        <span className="truncate text-text-primary">{link.source}</span>
        <Share2 className="h-3 w-3 shrink-0 text-text-muted" />
        <span className="truncate text-text-primary">{link.target}</span>
      </div>
      <div className="flex items-center gap-1 shrink-0 ml-2">
        <GitBranch className="h-3 w-3 text-text-muted" />
        <span className="text-xs text-text-muted">{link.weight}</span>
      </div>
    </div>
  );
}

function CentralityRow({ entry }: { entry: CentralityEntry }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-surface-active/30 px-3 py-2 text-sm">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {entry.type === "institution" ? (
          <Building2 className="h-4 w-4 shrink-0 text-text-muted" />
        ) : (
          <Users className="h-4 w-4 shrink-0 text-text-muted" />
        )}
        <span className="truncate text-text-primary">{entry.name}</span>
      </div>
      <span className="shrink-0 ml-2 text-xs text-text-muted">
        {entry.centrality.toFixed(3)}
      </span>
    </div>
  );
}

export function CollaborationList({ data }: CollaborationListProps) {
  const hasInstitutionCollabs = (data.institution_collaborations?.length ?? 0) > 0;
  const hasAuthorCollabs = (data.author_collaborations?.length ?? 0) > 0;
  const hasCentrality = (data.centrality_rankings?.length ?? 0) > 0;

  if (!hasInstitutionCollabs && !hasAuthorCollabs && !hasCentrality) {
    return (
      <p className="text-sm text-text-muted">
        No collaboration data available.
      </p>
    );
  }

  return (
    <div className="space-y-5">
      {/* Institution collaborations */}
      {hasInstitutionCollabs && (
        <div>
          <h3 className="mb-2 text-xs font-medium text-text-muted uppercase tracking-wider">
            Institution Collaborations
          </h3>
          <div className="space-y-1.5">
            {data.institution_collaborations.map((link, i) => (
              <CollaborationLinkRow
                key={`inst-${i}`}
                link={link}
                icon={Building2}
              />
            ))}
          </div>
        </div>
      )}

      {/* Author collaborations */}
      {hasAuthorCollabs && (
        <div>
          <h3 className="mb-2 text-xs font-medium text-text-muted uppercase tracking-wider">
            Author Collaborations
          </h3>
          <div className="space-y-1.5">
            {data.author_collaborations.map((link, i) => (
              <CollaborationLinkRow
                key={`auth-${i}`}
                link={link}
                icon={Users}
              />
            ))}
          </div>
        </div>
      )}

      {/* Edges count */}
      {data.total_edges > 0 && (
        <p className="text-xs text-text-muted">
          Total collaboration edges: {data.total_edges}
        </p>
      )}

      {/* Centrality rankings */}
      {hasCentrality && (
        <div>
          <h3 className="mb-2 text-xs font-medium text-text-muted uppercase tracking-wider">
            Centrality Rankings
          </h3>
          <div className="space-y-1.5">
            {data.centrality_rankings.map((entry, i) => (
              <CentralityRow key={`cent-${i}`} entry={entry} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
