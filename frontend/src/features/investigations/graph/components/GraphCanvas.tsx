import { useCallback, useMemo, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type NodeTypes,
  type EdgeTypes,
  SelectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { GraphDTO } from "../types/graph";
import { layoutGraph } from "../utils/layout";
import GraphNodeComponent from "./GraphNode";
import GraphEdgeComponent from "./GraphEdge";

const nodeTypes: NodeTypes = {
  graphNode: GraphNodeComponent,
};

const edgeTypes: EdgeTypes = {
  graphEdge: GraphEdgeComponent,
};

interface GraphCanvasProps {
  data: GraphDTO;
  searchQuery: string;
  onNodeSelect: (nodeId: string | null) => void;
}

export function GraphCanvas({ data, searchQuery, onNodeSelect }: GraphCanvasProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rfInstance = useRef<any>(null);

  const { nodes: baseNodes, edges: baseEdges } = useMemo(
    () => layoutGraph(data),
    [data],
  );

  const { nodes, edges } = useMemo((): { nodes: Node[]; edges: typeof baseEdges } => {
    if (!searchQuery.trim()) {
      return {
        nodes: baseNodes.map((n) => ({
          ...n,
          data: { ...n.data, isHighlighted: false, isDimmed: false },
        })),
        edges: baseEdges,
      };
    }

    const q = searchQuery.toLowerCase();
    const matchedIds = new Set<string>();

    for (const n of baseNodes) {
      if (String(n.data.label ?? "").toLowerCase().includes(q)) {
        matchedIds.add(n.id);
      }
    }

    return {
      nodes: baseNodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isHighlighted: matchedIds.has(n.id),
          isDimmed: !matchedIds.has(n.id),
        },
      })),
      edges: baseEdges,
    };
  }, [baseNodes, baseEdges, searchQuery]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeSelect(node.id);
    },
    [onNodeSelect],
  );

  const onPaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  return (
    <div className="h-full w-full" role="application" aria-label="Knowledge graph visualization">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onInit={(instance) => { rfInstance.current = instance; }}
        selectionMode={SelectionMode.Partial}
        fitView
        minZoom={0.1}
        maxZoom={3}
        onlyRenderVisibleElements
        attributionPosition="bottom-left"
      >
        <Background color="#e5e7eb" gap={20} size={1} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            const colors: Record<string, string> = {
              paper: "#3b82f6",
              author: "#10b981",
              institution: "#f97316",
              dataset: "#a855f7",
              technology: "#06b6d4",
              methodology: "#ec4899",
              research_domain: "#f59e0b",
            };
            return colors[(n.data as { nodeType?: string })?.nodeType ?? ""] ?? "#6b7280";
          }}
          pannable
          zoomable
          className="!border !border-border"
        />
      </ReactFlow>
    </div>
  );
}
