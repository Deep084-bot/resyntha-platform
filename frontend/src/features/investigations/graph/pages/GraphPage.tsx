import { useCallback, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { useGraph } from "../hooks/useGraph";
import type { NodeType } from "../types/graph";
import {
  GraphCanvas,
  GraphEmptyState,
  GraphFilters,
  GraphSearch,
  GraphSkeleton,
  NodeDetailPanel,
} from "../components";
import { RunningMessage } from "@/features/investigations/components/RunningMessage";
import { useInvestigationRun } from "@/features/investigations/layout/InvestigationRunContext";

export function GraphPage() {
  const { id } = useParams();
  const { data, isLoading, isError, error, isEmpty } = useGraph(id);
  const { running } = useInvestigationRun();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilters, setActiveFilters] = useState<Set<NodeType> | null>(null);

  const availableTypes: NodeType[] = useMemo(() => {
    if (!data) return [];
    const types = new Set(data.nodes.map((n) => n.type));
    return Array.from(types);
  }, [data]);

  const filteredNodes = useMemo(() => {
    if (!data) return [];
    const active = activeFilters ?? new Set(availableTypes);
    if (active.size === 0) return [];
    return data.nodes.filter((n) => active.has(n.type));
  }, [data, activeFilters, availableTypes]);

  const selectedNode = useMemo(() => {
    if (!selectedNodeId || !data) return null;
    return data.nodes.find((n) => n.id === selectedNodeId) ?? null;
  }, [selectedNodeId, data]);

  const handleNodeSelect = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
  }, []);

  const handleClosePanel = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  if (isLoading) {
    return <GraphSkeleton />;
  }

  if (isError) {
    return (
      <div
        className="flex h-64 flex-col items-center justify-center gap-2 text-sm text-text-muted"
        role="alert"
      >
        <p>Failed to load research graph.</p>
        {error && <p className="text-xs">{error.message}</p>}
      </div>
    );
  }

  if (isEmpty || !data) {
    if (running) {
      return (
        <div className="space-y-4">
          <RunningMessage phase="Building knowledge graph" />
          <GraphSkeleton />
        </div>
      );
    }
    return <GraphEmptyState />;
  }

  const filteredData = useMemo(() => ({
    ...data,
    nodes: filteredNodes,
    edges: data.edges.filter(
      (e) =>
        filteredNodes.some((n) => n.id === e.source) &&
        filteredNodes.some((n) => n.id === e.target),
    ),
  }), [data, filteredNodes]);

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <GraphFilters
          filters={{ nodeTypes: activeFilters ?? new Set(availableTypes), searchQuery }}
          onChange={(f) => setActiveFilters(f.nodeTypes)}
          availableTypes={availableTypes}
        />
        <GraphSearch value={searchQuery} onChange={setSearchQuery} />
      </div>

      {/* Graph + side panel */}
      <div className="flex flex-1 gap-0 overflow-hidden rounded-md border border-border">
        <div className="flex-1">
          <GraphCanvas
            data={filteredData}
            searchQuery={searchQuery}
            onNodeSelect={handleNodeSelect}
          />
        </div>

        {selectedNode && (
          <div className="w-80 shrink-0">
            <NodeDetailPanel node={selectedNode} onClose={handleClosePanel} />
          </div>
        )}
      </div>

      {/* Metadata footer */}
      <div className="flex items-center gap-4 text-[11px] text-text-muted">
        <span>{data.metadata.total_nodes} nodes</span>
        <span>{data.metadata.total_edges} edges</span>
        {Object.entries(data.metadata.node_counts).map(([type, count]) => (
          <span key={type}>
            {count} {type}s
          </span>
        ))}
      </div>
    </div>
  );
}


