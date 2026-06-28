import type { StatusVariant } from "@/components/ui/status-badge";

/* ── Enums ──────────────────────────────────────────────────── */

export type InvestigationStatus =
  | "created"
  | "planning"
  | "retrieving"
  | "validating"
  | "extracting"
  | "analyzing"
  | "generating"
  | "completed"
  | "failed"
  | "cancelled";

export type TimelineStage =
  | "created"
  | "planning"
  | "retrieving"
  | "validating"
  | "extracting"
  | "analyzing"
  | "generating"
  | "completed"
  | "failed"
  | "cancelled";

export type TimelineStatus =
  | "success"
  | "failure"
  | "pending"
  | "running";

export type ArtifactType =
  | "execution_plan"
  | "paper_collection"
  | "validated_collection"
  | "knowledge_package"
  | "comparison_matrix"
  | "trend_report"
  | "opportunity_report"
  | "research_ideas"
  | "final_report";

export type ArtifactStatus =
  | "pending"
  | "generating"
  | "ready"
  | "failed";

/* ── Domain models ──────────────────────────────────────────── */

export interface Investigation {
  id: string;
  title: string;
  topic: string;
  status: InvestigationStatus;
  paper_limit: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown> | null;
}

export interface CreateInvestigationRequest {
  title: string;
  topic: string;
  paper_limit?: number;
}

export interface TimelineEvent {
  stage: TimelineStage;
  status: TimelineStatus;
  message: string;
  created_at: string;
}

export interface Artifact {
  id: string;
  investigation_id: string;
  artifact_type: ArtifactType;
  version: number;
  status: ArtifactStatus;
  payload: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Paper {
  id: string;
  title: string;
  abstract: string | null;
  doi: string | null;
  venue: string | null;
  year: number | null;
  citation_count: number | null;
  url: string | null;
  created_at: string;
  updated_at: string;
}

export interface RetrieveRequest {
  query: string;
  paper_limit?: number;
}

export interface RetrieveResponse {
  investigation_id: string;
  artifact_id: string;
  paper_count: number;
}

/* ── Status mappers (API → StatusBadge) ─────────────────────── */

const INVESTIGATION_MAP: Record<InvestigationStatus, StatusVariant> = {
  created: "pending",
  planning: "pending",
  retrieving: "running",
  validating: "running",
  extracting: "running",
  analyzing: "running",
  generating: "running",
  completed: "success",
  failed: "failure",
  cancelled: "skipped",
};

export function mapInvestigationStatus(s: InvestigationStatus): StatusVariant {
  return INVESTIGATION_MAP[s];
}

const TIMELINE_MAP: Record<TimelineStatus, StatusVariant> = {
  success: "success",
  failure: "failure",
  pending: "pending",
  running: "running",
};

export function mapTimelineStatus(s: TimelineStatus): StatusVariant {
  return TIMELINE_MAP[s];
}

const ARTIFACT_MAP: Record<ArtifactStatus, StatusVariant> = {
  pending: "pending",
  generating: "running",
  ready: "success",
  failed: "failure",
};

export function mapArtifactStatus(s: ArtifactStatus): StatusVariant {
  return ARTIFACT_MAP[s];
}

/* ── Query key factory ──────────────────────────────────────── */

export const queryKeys = {
  investigations: {
    all: ["investigations"] as const,
    detail: (id: string) => ["investigations", id] as const,
    timeline: (id: string) => ["investigations", id, "timeline"] as const,
  },
  artifacts: {
    byInvestigation: (id: string) => ["investigations", id, "artifacts"] as const,
  },
  papers: {
    byInvestigation: (id: string) => ["investigations", id, "papers"] as const,
  },
} as const;
