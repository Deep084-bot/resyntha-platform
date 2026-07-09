export type NodeType =
  | "paper"
  | "author"
  | "institution"
  | "dataset"
  | "technology"
  | "methodology"
  | "research_domain";

export interface GraphNodeDTO {
  id: string;
  type: NodeType;
  label: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdgeDTO {
  id: string;
  source: string;
  target: string;
  label: string;
  type: string;
}

export interface GraphMetadataDTO {
  total_nodes: number;
  total_edges: number;
  node_counts: Record<string, number>;
  edge_counts: Record<string, number>;
}

export interface GraphDTO {
  nodes: GraphNodeDTO[];
  edges: GraphEdgeDTO[];
  metadata: GraphMetadataDTO;
}
