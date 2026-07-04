/* ── Top-level landscape response ─────────────────────────────── */

export interface LandscapeData {
  overview: LandscapeOverview;
  observations: Observation[];
  institutions: Institution[];
  methodologies: Methodology[];
  technologies: Technology[];
  datasets: Dataset[];
  temporal_trends: TemporalTrend[];
  collaborations: CollaborationData;
}

/* ── Overview ─────────────────────────────────────────────────── */

export interface LandscapeOverview {
  total_papers: number;
  years_covered: string;
  total_institutions: number;
  total_technologies: number;
  total_datasets: number;
  total_methodologies: number;
  total_authors: number;
}

/* ── Observations ─────────────────────────────────────────────── */

export interface Observation {
  category: string;
  label: string;
  value: string;
}

/* ── Institutions ─────────────────────────────────────────────── */

export interface Institution {
  name: string;
  type: string;
  paper_count: number;
  author_count: number;
}

/* ── Methodologies ────────────────────────────────────────────── */

export interface Methodology {
  name: string;
  technique_count: number;
  paper_count: number;
}

/* ── Technologies ─────────────────────────────────────────────── */

export interface Technology {
  name: string;
  first_appearance_year: number | null;
  paper_count: number;
}

/* ── Datasets ─────────────────────────────────────────────────── */

export interface Dataset {
  name: string;
  usage_count: number;
  diversity_metric: number | null;
}

/* ── Temporal Trends ──────────────────────────────────────────── */

export interface TemporalTrend {
  year: number;
  paper_count: number;
  methodology_adoptions: number;
  technology_adoptions: number;
  dataset_usage_count: number;
}

/* ── Collaborations ───────────────────────────────────────────── */

export interface CollaborationData {
  institution_collaborations: CollaborationLink[];
  author_collaborations: CollaborationLink[];
  centrality_rankings: CentralityEntry[];
  total_edges: number;
}

export interface CollaborationLink {
  source: string;
  target: string;
  weight: number;
}

export interface CentralityEntry {
  name: string;
  centrality: number;
  type: "institution" | "author";
}
