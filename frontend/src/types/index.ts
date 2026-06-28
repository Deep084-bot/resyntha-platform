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
  | "research_landscape"
  | "research_gap_report"
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

export type ExecutionStatus =
  | "pending"
  | "running"
  | "failed"
  | "completed"
  | "cancelled";

export type ExecutionStageStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

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

export interface RetrieveAcceptedResponse {
  execution_id: string;
  status: string;
  queue_position?: number | null;
}

export interface Execution {
  id: string;
  investigation_id: string;
  status: ExecutionStatus;
  trigger: string;
  created_by: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

export interface ExecutionStage {
  id: string;
  execution_id: string;
  stage_name: string;
  status: ExecutionStageStatus;
  attempt: number;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
  created_at: string;
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

const EXECUTION_MAP: Record<ExecutionStatus, StatusVariant> = {
  pending: "pending",
  running: "running",
  failed: "failure",
  completed: "success",
  cancelled: "skipped",
};

export function mapExecutionStatus(s: ExecutionStatus): StatusVariant {
  return EXECUTION_MAP[s];
}

const STAGE_MAP: Record<ExecutionStageStatus, StatusVariant> = {
  pending: "pending",
  running: "running",
  completed: "success",
  failed: "failure",
  skipped: "skipped",
};

export function mapStageStatus(s: ExecutionStageStatus): StatusVariant {
  return STAGE_MAP[s];
}

export function isExecutionTerminal(s: ExecutionStatus): boolean {
  return s === "completed" || s === "failed" || s === "cancelled";
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
  executions: {
    byInvestigation: (id: string) => ["investigations", id, "executions"] as const,
    detail: (id: string) => ["executions", id] as const,
    stages: (id: string) => ["executions", id, "stages"] as const,
  },
} as const;
