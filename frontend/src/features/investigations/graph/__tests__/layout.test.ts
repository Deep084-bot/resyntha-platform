import { describe, expect, it } from "vitest";

import { layoutGraph } from "../utils/layout";
import type { GraphDTO } from "../types/graph";

const emptyGraph: GraphDTO = {
  nodes: [],
  edges: [],
  metadata: { total_nodes: 0, total_edges: 0, node_counts: {}, edge_counts: {} },
};

const singlePaperGraph: GraphDTO = {
  nodes: [
    { id: "paper:p1", type: "paper", label: "Paper 1", metadata: {} },
    { id: "author:a1", type: "author", label: "Author 1", metadata: {} },
  ],
  edges: [
    { id: "paper:p1->author:a1", source: "paper:p1", target: "author:a1", label: "AUTHORED_BY", type: "AUTHORED_BY" },
  ],
  metadata: { total_nodes: 2, total_edges: 1, node_counts: { paper: 1, author: 1 }, edge_counts: { AUTHORED_BY: 1 } },
};

describe("layoutGraph", () => {
  it("returns empty arrays for empty graph", () => {
    const { nodes, edges } = layoutGraph(emptyGraph);
    expect(nodes).toHaveLength(0);
    expect(edges).toHaveLength(0);
  });

  it("creates React Flow nodes with correct data", () => {
    const { nodes } = layoutGraph(singlePaperGraph);
    const paperNode = nodes.find((n) => n.id === "paper:p1");
    expect(paperNode).toBeDefined();
    expect(paperNode!.type).toBe("graphNode");
    expect(paperNode!.data.label).toBe("Paper 1");
    expect(paperNode!.data.nodeType).toBe("paper");
  });

  it("creates React Flow edges", () => {
    const { edges } = layoutGraph(singlePaperGraph);
    expect(edges).toHaveLength(1);
    expect(edges[0]!.source).toBe("paper:p1");
    expect(edges[0]!.target).toBe("author:a1");
  });

  it("assigns positions to nodes", () => {
    const { nodes } = layoutGraph(singlePaperGraph);
    for (const node of nodes) {
      expect(typeof node.position.x).toBe("number");
      expect(typeof node.position.y).toBe("number");
    }
  });

  it("filters out edges where source or target is missing from nodes", () => {
    const graphWithOrphanEdge: GraphDTO = {
      nodes: [{ id: "paper:p1", type: "paper", label: "P1", metadata: {} }],
      edges: [
        { id: "e1", source: "paper:p1", target: "nonexistent", label: "AUTHORED_BY", type: "AUTHORED_BY" },
      ],
      metadata: { total_nodes: 1, total_edges: 1, node_counts: { paper: 1 }, edge_counts: { AUTHORED_BY: 1 } },
    };
    const { edges } = layoutGraph(graphWithOrphanEdge);
    expect(edges).toHaveLength(0);
  });
});
