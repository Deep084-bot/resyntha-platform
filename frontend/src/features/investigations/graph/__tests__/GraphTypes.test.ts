import { describe, expect, it } from "vitest";

import type { GraphDTO, GraphEdgeDTO, GraphNodeDTO, GraphMetadataDTO, NodeType } from "../types/graph";

describe("GraphDTO types", () => {
  it("validates a complete graph DTO shape", () => {
    const graph: GraphDTO = {
      nodes: [
        { id: "p1", type: "paper", label: "Paper 1", metadata: { year: 2024 } },
        { id: "a1", type: "author", label: "Author 1", metadata: {} },
      ],
      edges: [
        { id: "e1", source: "p1", target: "a1", label: "AUTHORED_BY", type: "AUTHORED_BY" },
      ],
      metadata: {
        total_nodes: 2,
        total_edges: 1,
        node_counts: { paper: 1, author: 1 },
        edge_counts: { AUTHORED_BY: 1 },
      },
    };
    expect(graph.nodes).toHaveLength(2);
    expect(graph.edges).toHaveLength(1);
    expect(graph.metadata.total_nodes).toBe(2);
  });

  it("supports all node types", () => {
    const types: NodeType[] = [
      "paper", "author", "institution", "dataset",
      "technology", "methodology", "research_domain",
    ];
    const nodes: GraphNodeDTO[] = types.map((t, i) => ({
      id: `${t}:${i}`,
      type: t,
      label: `Node ${i}`,
      metadata: {},
    }));
    expect(nodes).toHaveLength(7);
  });

  it("supports flexible metadata", () => {
    const node: GraphNodeDTO = {
      id: "paper:1",
      type: "paper",
      label: "Test",
      metadata: {
        year: 2024,
        authors: ["A", "B"],
        custom_field: { nested: true },
      },
    };
    expect(node.metadata.year).toBe(2024);
    expect(node.metadata.custom_field.nested).toBe(true);
  });

  it("validates edge shape", () => {
    const edge: GraphEdgeDTO = {
      id: "p1->a1",
      source: "p1",
      target: "a1",
      label: "AUTHORED_BY",
      type: "AUTHORED_BY",
    };
    expect(edge.source).toBe("p1");
    expect(edge.target).toBe("a1");
  });

  it("supports empty graph", () => {
    const graph: GraphDTO = {
      nodes: [],
      edges: [],
      metadata: { total_nodes: 0, total_edges: 0, node_counts: {}, edge_counts: {} },
    };
    expect(graph.nodes).toHaveLength(0);
    expect(graph.metadata.total_nodes).toBe(0);
  });
});
