import { X } from "lucide-react";

import type { GraphNodeDTO, NodeType } from "../types/graph";

interface NodeDetailPanelProps {
  node: GraphNodeDTO;
  onClose: () => void;
}

function DetailRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex justify-between gap-2 text-xs">
      <span className="text-text-muted shrink-0">{label}</span>
      <span className="text-text-primary text-right">{String(value)}</span>
    </div>
  );
}

function DetailList({ label, items }: { label: string; items: (string | unknown)[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-1">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
        {label}
      </span>
      <div className="flex flex-wrap gap-1">
        {items.slice(0, 10).map((item, i) => (
          <span
            key={i}
            className="inline-block rounded bg-surface-hover px-1.5 py-0.5 text-[11px] text-text-secondary"
          >
            {String(item)}
          </span>
        ))}
        {items.length > 10 && (
          <span className="text-[11px] text-text-muted">+{items.length - 10} more</span>
        )}
      </div>
    </div>
  );
}

export function NodeDetailPanel({ node, onClose }: NodeDetailPanelProps) {
  const m = node.metadata;

  const nodeTypeLabel: Record<NodeType, string> = {
    paper: "Paper",
    author: "Author",
    institution: "Institution",
    dataset: "Dataset",
    technology: "Technology",
    methodology: "Methodology",
    research_domain: "Research Domain",
  };

  return (
    <div className="flex h-full flex-col border-l border-border bg-card" role="dialog" aria-label={`${nodeTypeLabel[node.type] ?? "Node"} details`}>
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold text-text-primary">
          {nodeTypeLabel[node.type] ?? "Node"}
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-text-muted hover:bg-surface-hover hover:text-text-primary transition-colors"
          aria-label="Close detail panel"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-text-primary leading-snug">{node.label}</h4>
          </div>

          {node.type === "paper" && (
            <div className="space-y-3">
              <DetailRow label="Year" value={m.year as number | null} />
              <DetailRow label="Citations" value={m.citation_count as number | null} />
              <DetailRow label="Venue" value={m.venue as string | null} />
              <DetailList label="Authors" items={m.authors as string[]} />
              <DetailList label="Institutions" items={m.institutions as string[]} />
              <DetailList label="Methodologies" items={m.methodology as string[]} />
              <DetailList label="Datasets" items={m.datasets as string[]} />
              <DetailList label="Technologies" items={m.technologies as string[]} />
              <DetailList label="Research Domains" items={m.research_domains as string[]} />
              {(m.summary as string) && (
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Summary</span>
                  <p className="text-[11px] text-text-secondary leading-relaxed">{m.summary as string}</p>
                </div>
              )}
            </div>
          )}

          {node.type === "author" && (
            <div className="space-y-3">
              <DetailList label="Papers" items={m.papers as string[]} />
              <DetailRow label="Institution" value={m.institution as string | null} />
              <DetailRow label="First Publication Year" value={m.first_publication_year as number | null} />
            </div>
          )}

          {node.type === "institution" && (
            <div className="space-y-3">
              <DetailRow label="Type" value={m.type as string | null} />
              <DetailRow label="Country" value={m.country as string | null} />
              <DetailRow label="Paper Count" value={m.paper_count as number | null} />
              <DetailList label="Authors" items={m.author_names as string[]} />
            </div>
          )}

          {(node.type === "dataset" || node.type === "research_domain") && (
            <div className="space-y-3">
              <DetailList label="Related Papers" items={m.related_papers as string[]} />
            </div>
          )}

          {node.type === "technology" && (
            <div className="space-y-3">
              <DetailRow label="Type" value={m.type as string | null} />
              <DetailList label="Related Papers" items={m.related_papers as string[]} />
            </div>
          )}

          {node.type === "methodology" && (
            <div className="space-y-3">
              <DetailList label="Related Papers" items={m.related_papers as string[]} />
              <DetailList label="Techniques" items={m.techniques as string[]} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
