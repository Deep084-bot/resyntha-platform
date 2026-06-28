import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  FlaskConical,
  Lightbulb,
  ListTree,
  Search,
  TrendingUp,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useArtifacts } from "@/hooks/useArtifacts";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { StatusVariant } from "@/components/ui/status-badge";

type GapCategory =
  | "dataset"
  | "methodology"
  | "evaluation"
  | "future_work"
  | "limitation"
  | "method_combination"
  | "temporal";

type GapSeverity = "high" | "medium" | "low";

interface Evidence {
  description: string;
  supporting_paper_ids: string[];
  supporting_facts: string[];
  statistics: Record<string, number>;
}

interface Gap {
  id: string;
  title: string;
  description: string;
  category: GapCategory;
  confidence: number;
  severity: GapSeverity;
  evidence: Evidence;
  recommendation: string;
}

interface GapSummary {
  total_gaps: number;
  high_confidence_gaps: number;
  categories: Record<string, number>;
  severities: Record<string, number>;
}

interface ResearchGapReport {
  summary: GapSummary;
  gaps: Gap[];
  statistics: Record<string, number>;
  recommendations: string[];
  generated_at: string;
}

/* ── Helpers ─────────────────────────────────────────────────── */

const CATEGORY_LABELS: Record<GapCategory, string> = {
  dataset: "Dataset",
  methodology: "Methodology",
  evaluation: "Evaluation",
  future_work: "Future Work",
  limitation: "Limitation",
  method_combination: "Method Combination",
  temporal: "Temporal",
};

const CATEGORY_ICONS: Record<GapCategory, React.ReactNode> = {
  dataset: <BarChart3 className="h-4 w-4" />,
  methodology: <FlaskConical className="h-4 w-4" />,
  evaluation: <CheckCircle2 className="h-4 w-4" />,
  future_work: <Lightbulb className="h-4 w-4" />,
  limitation: <AlertTriangle className="h-4 w-4" />,
  method_combination: <ListTree className="h-4 w-4" />,
  temporal: <TrendingUp className="h-4 w-4" />,
};

function severityVariant(s: GapSeverity): StatusVariant {
  return s === "high" ? "failure" : s === "medium" ? "warning" : "pending";
}

function confidenceLabel(c: number): string {
  if (c >= 0.7) return "High";
  if (c >= 0.4) return "Medium";
  return "Low";
}

function confidenceVariant(c: number): StatusVariant {
  if (c >= 0.7) return "success";
  if (c >= 0.4) return "warning";
  return "pending";
}

/* ── Stat Card ────────────────────────────────────────────────── */

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-text-muted">
          {label}
        </CardTitle>
        <div className="h-4 w-4 text-text-muted">{icon}</div>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
      </CardContent>
    </Card>
  );
}

/* ── Filter Controls ─────────────────────────────────────────── */

function FilterBar({
  categories,
  activeCategory,
  onCategoryChange,
  sortBy,
  onSortChange,
}: {
  categories: string[];
  activeCategory: string;
  onCategoryChange: (c: string) => void;
  sortBy: string;
  onSortChange: (s: string) => void;
}) {
  const allCategories = ["all", ...categories];
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1.5 text-xs text-text-muted">
        <Search className="h-3 w-3" />
        <span>Filter:</span>
      </div>
      <div className="flex flex-wrap gap-1">
        {allCategories.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => onCategoryChange(cat)}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
              cat === activeCategory
                ? "bg-accent-default text-white"
                : "bg-surface-card text-text-muted hover:text-text-primary",
            )}
          >
            {cat === "all" ? "All" : CATEGORY_LABELS[cat as GapCategory] ?? cat}
          </button>
        ))}
      </div>
      <div className="ml-auto flex items-center gap-2 text-xs text-text-muted">
        <span>Sort:</span>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          className="rounded-md border border-border bg-surface-card px-2 py-1 text-xs text-text-primary"
        >
          <option value="confidence">Confidence</option>
          <option value="severity">Severity</option>
        </select>
      </div>
    </div>
  );
}

/* ── Gap Card ─────────────────────────────────────────────────── */

function GapCard({ gap }: { gap: Gap }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              {CATEGORY_ICONS[gap.category]}
              <h3 className="text-sm font-semibold text-text-primary leading-snug">
                {gap.title}
              </h3>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-medium text-text-muted uppercase tracking-wider">
                {CATEGORY_LABELS[gap.category]}
              </span>
              <StatusBadge
                status={confidenceVariant(gap.confidence)}
                label={confidenceLabel(gap.confidence)}
              />
              <StatusBadge
                status={severityVariant(gap.severity)}
                label={gap.severity}
              />
            </div>
          </div>
        </div>

        <p className="mt-2 text-sm text-text-secondary leading-relaxed">
          {gap.description}
        </p>

        {gap.evidence.supporting_facts.length > 0 && (
          <div className="mt-2 space-y-0.5">
            {gap.evidence.supporting_facts.map((fact, i) => (
              <p
                key={i}
                className="flex items-center gap-1.5 text-xs text-text-muted"
              >
                <span className="inline-block h-1 w-1 rounded-full bg-accent-default shrink-0" />
                {fact}
              </p>
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-xs text-accent-default hover:underline"
        >
          {expanded ? "Hide details" : "Show details"}
        </button>

        {expanded && (
          <div className="mt-2 space-y-2 border-t border-border pt-2">
            {gap.recommendation && (
              <div>
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                  Recommendation
                </p>
                <p className="text-sm text-text-primary mt-0.5">
                  {gap.recommendation}
                </p>
              </div>
            )}
            {gap.evidence.statistics &&
              Object.keys(gap.evidence.statistics).length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Statistics
                  </p>
                  <div className="mt-0.5 grid grid-cols-2 gap-1 sm:grid-cols-3">
                    {Object.entries(gap.evidence.statistics).map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="rounded bg-surface-card px-2 py-1"
                        >
                          <p className="text-[10px] text-text-muted">
                            {key.replace(/_/g, " ")}
                          </p>
                          <p className="text-xs font-medium text-text-primary">
                            {value}
                          </p>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ── Main Page ────────────────────────────────────────────────── */

export function WorkspaceResearchGapsPage() {
  const { id } = useParams();
  const { data: artifacts, isLoading, isError } = useArtifacts(id);

  const [activeCategory, setActiveCategory] = useState("all");
  const [sortBy, setSortBy] = useState("confidence");

  const gapArtifact = useMemo(() => {
    const filtered = (artifacts ?? []).filter(
      (a) => a.artifact_type === "research_gap_report",
    );
    return filtered.length > 0
      ? filtered.sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime(),
        )[0]
      : null;
  }, [artifacts]);

  const report = gapArtifact?.payload as ResearchGapReport | null;

  const categories = useMemo(() => {
    if (!report) return [];
    return Object.keys(report.summary.categories);
  }, [report]);

  const filteredGaps = useMemo(() => {
    if (!report) return [];
    let gaps = [...report.gaps];
    if (activeCategory !== "all") {
      gaps = gaps.filter((g) => g.category === activeCategory);
    }
    gaps.sort((a, b) => {
      if (sortBy === "confidence") return b.confidence - a.confidence;
      const sevOrder = { high: 3, medium: 2, low: 1 };
      return (sevOrder[b.severity] ?? 0) - (sevOrder[a.severity] ?? 0);
    });
    return gaps;
  }, [report, activeCategory, sortBy]);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Research Gaps"
        description="Deterministic gap analysis across extracted paper knowledge"
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-32 w-full rounded-lg" />
          <Skeleton className="h-32 w-full rounded-lg" />
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">
          Failed to load gap detection data.
        </p>
      ) : report ? (
        <>
          {/* Stat cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={<BrainCircuit className="h-4 w-4" />}
              label="Total Gaps"
              value={report.summary.total_gaps}
            />
            <StatCard
              icon={<CheckCircle2 className="h-4 w-4" />}
              label="High Confidence"
              value={report.summary.high_confidence_gaps}
            />
            <StatCard
              icon={<BarChart3 className="h-4 w-4" />}
              label="Dataset Gaps"
              value={report.summary.categories.dataset ?? 0}
            />
            <StatCard
              icon={<FlaskConical className="h-4 w-4" />}
              label="Methodology Gaps"
              value={
                (report.summary.categories.methodology ?? 0) +
                (report.summary.categories.method_combination ?? 0)
              }
            />
          </div>

          {report.generated_at && (
            <p className="text-xs text-text-muted">
              Analyzed: {formatDateTime(report.generated_at)}
            </p>
          )}

          {/* Recommendations */}
          {report.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <Lightbulb className="h-4 w-4" />
                  Key Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {report.recommendations.slice(0, 5).map((rec, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-text-secondary"
                    >
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-default" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Filter + sort */}
          <FilterBar
            categories={categories}
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
            sortBy={sortBy}
            onSortChange={setSortBy}
          />

          {/* Gap cards */}
          <div className="space-y-3">
            {filteredGaps.length > 0 ? (
              filteredGaps.map((gap) => (
                <GapCard key={gap.id} gap={gap} />
              ))
            ) : (
              <div className="flex h-24 items-center justify-center rounded-lg border border-dashed border-border">
                <p className="text-sm text-text-muted">
                  No gaps match the selected filter.
                </p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-border">
          <div className="flex flex-col items-center gap-2 text-sm text-text-muted">
            <Search className="h-8 w-8" />
            <p>
              No gap analysis available. Run the retrieval pipeline with
              knowledge extraction and analysis to generate gap reports.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
