import type { Node, Edge } from "@xyflow/react";

import type { GraphDTO, NodeType } from "../types/graph";

const TYPE_COLUMN: Record<NodeType, number> = {
  paper: 0,
  author: 1,
  institution: 2,
  methodology: 3,
  dataset: 3,
  technology: 3,
  research_domain: 4,
};

const COLUMN_X: Record<number, number> = {
  0: 50,
  1: 350,
  2: 650,
  3: 950,
  4: 1250,
};

const NODE_HEIGHT = 80;
const NODE_GAP = 30;

export function layoutGraph(dto: GraphDTO): { nodes: Node[]; edges: Edge[] } {
  const typeGroups: Record<string, { id: string; type: NodeType; label: string; metadata: Record<string, unknown> }[]> = {};

  for (const n of dto.nodes) {
    const t = n.type;
    if (!typeGroups[t]) typeGroups[t] = [];
    typeGroups[t].push(n);
  }

  const nodes: Node[] = [];
  let currentY = 30;

  const sortedTypes = Object.keys(typeGroups).sort(
    (a, b) => (TYPE_COLUMN[a as NodeType] ?? 99) - (TYPE_COLUMN[b as NodeType] ?? 99),
  );

  const typeOffsets: Record<string, number> = {};
  for (const t of sortedTypes) {
    const col = TYPE_COLUMN[t as NodeType] ?? 0;
    const items = typeGroups[t];
    if (!items) continue;

    if (col === 0) {
      typeOffsets[t] = currentY;
      for (let i = 0; i < items.length; i++) {
        const item = items[i]!;
        nodes.push({
          id: item.id,
          type: "graphNode",
          position: { x: COLUMN_X[col] ?? 0, y: currentY + i * (NODE_HEIGHT + NODE_GAP) },
          data: {
            label: item.label,
            nodeType: item.type,
            metadata: item.metadata,
            isHighlighted: false,
            isDimmed: false,
          },
        });
      }
    }
  }

  const paperCount = typeGroups["paper"]?.length ?? 0;
  const maxEntityY = paperCount > 0
    ? typeOffsets["paper"] !== undefined
      ? typeOffsets["paper"] + paperCount * (NODE_HEIGHT + NODE_GAP)
      : 0
    : 0;

  for (const t of sortedTypes) {
    const col = TYPE_COLUMN[t as NodeType] ?? 0;
    if (col === 0) continue;
    const items = typeGroups[t];
    if (!items) continue;

    const startY = Math.max(currentY, maxEntityY - items.length * (NODE_HEIGHT + NODE_GAP) / 2);
    for (let i = 0; i < items.length; i++) {
      const item = items[i]!;
      nodes.push({
        id: item.id,
        type: "graphNode",
        position: { x: COLUMN_X[col] ?? 0, y: startY + i * (NODE_HEIGHT + NODE_GAP) },
        data: {
          label: item.label,
          nodeType: item.type,
          metadata: item.metadata,
          isHighlighted: false,
          isDimmed: false,
        },
      });
    }
  }

  const nodeIds = new Set(nodes.map((n) => n.id));
  const edges: Edge[] = dto.edges
    .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
    .map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: "graphEdge",
      data: { label: e.label },
    }));

  return { nodes, edges };
}
