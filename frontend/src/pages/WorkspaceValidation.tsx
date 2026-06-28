import { useParams } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  AlertTriangle,
  Clock,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useArtifacts } from "@/hooks/useArtifacts";
import { formatDateTime } from "@/lib/format";
import { mapArtifactStatus, type Artifact, type ArtifactType } from "@/types";

interface ValidatedPaper {
  paper: Record<string, unknown>;
  validation_status: "valid" | "warning" | "invalid";
  validation_messages: string[];
  validation_score: number;
  validation_timestamp: string;
}

interface ValidationSummary {
  total_papers: number;
  valid: number;
  warning: number;
  invalid: number;
  duplicates: number;
  average_score: number;
  timestamp: string;
}

interface ValidationPayload {
  validated_papers: ValidatedPaper[];
  summary: ValidationSummary;
  generated_at: string;
}

function ValidationSummaryCards({ summary }: { summary: ValidationSummary }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-text-muted">Total Papers</CardTitle>
          <FileText className="h-4 w-4 text-text-muted" />
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-text-primary">{summary.total_papers}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-green-600">Valid</CardTitle>
          <CheckCircle2 className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-green-600">{summary.valid}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-yellow-600">Warning</CardTitle>
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-yellow-600">{summary.warning}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-red-600">Invalid</CardTitle>
          <AlertCircle className="h-4 w-4 text-red-600" />
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-red-600">{summary.invalid}</p>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusBadgeForScore({ status }: { status: string }) {
  const variant =
    status === "valid" ? "success" : status === "warning" ? "warning" : "failure";
  return <StatusBadge status={variant} label={status} />;
}

function ValidatedPaperCard({ paper }: { paper: ValidatedPaper }) {
  const title = (paper.paper?.title as string) ?? "Untitled";
  const doi = (paper.paper?.doi as string) ?? null;
  const venue = (paper.paper?.venue as string) ?? null;
  const year = (paper.paper?.year as number) ?? null;

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium text-text-primary">{title}</p>
              <StatusBadgeForScore status={paper.validation_status} />
            </div>
            <div className="mt-1 flex items-center gap-3 text-xs text-text-muted">
              {venue && <span>{venue}</span>}
              {year && <span>{year}</span>}
              {doi && (
                <span className="font-mono text-[10px] truncate max-w-[200px]">
                  {doi}
                </span>
              )}
              <span className="font-medium">Score: {paper.validation_score}</span>
            </div>
          </div>
        </div>

        {paper.validation_messages.length > 0 && (
          <div className="mt-2 space-y-1">
            {paper.validation_messages.map((msg, i) => (
              <p key={i} className="text-xs text-text-muted flex items-center gap-1.5">
                <span className="inline-block h-1 w-1 rounded-full bg-current shrink-0" />
                {msg}
              </p>
            ))}
          </div>
        )}

        {paper.validation_messages.length === 0 && paper.validation_status === "valid" && (
          <p className="mt-1 text-xs text-green-600">No issues</p>
        )}
      </CardContent>
    </Card>
  );
}

export function WorkspaceValidationPage() {
  const { id } = useParams();
  const { data: artifacts, isLoading, isError } = useArtifacts(id);

  const validationArtifacts = (artifacts ?? []).filter(
    (a) => a.artifact_type === "validated_collection",
  );

  const latestValidation: Artifact | null =
    validationArtifacts.length > 0
      ? validationArtifacts.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        )[0]
      : null;

  const payload = latestValidation?.payload as ValidationPayload | null;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Validation"
        description="Deterministic validation results for retrieved papers"
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-20 w-full rounded-lg" />
          <Skeleton className="h-20 w-full rounded-lg" />
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">Failed to load validation data.</p>
      ) : payload ? (
        <>
          {/* Summary */}
          <ValidationSummaryCards summary={payload.summary} />

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Validated: {formatDateTime(payload.generated_at)}
            </span>
            <span>Average score: {payload.summary.average_score}</span>
            {payload.summary.duplicates > 0 && (
              <span>Duplicates found: {payload.summary.duplicates}</span>
            )}
          </div>

          {/* Per-paper results */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-text-primary">
              Paper Results ({payload.validated_papers.length})
            </h3>
            {payload.validated_papers.map((vp, i) => (
              <ValidatedPaperCard key={i} paper={vp} />
            ))}
          </div>
        </>
      ) : (
        <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-border">
          <p className="text-sm text-text-muted">
            No validation data available. Run the retrieval pipeline to generate validation results.
          </p>
        </div>
      )}
    </div>
  );
}
