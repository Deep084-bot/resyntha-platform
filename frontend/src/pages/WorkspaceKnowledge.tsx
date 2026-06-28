import { useParams } from "react-router-dom";
import {
  BookOpen,
  BrainCircuit,
  FileText,
  Lightbulb,
  ListTree,
  Quote,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";

import { useArtifacts } from "@/hooks/useArtifacts";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

interface ExtractedPaperKnowledge {
  paper_id: string;
  paper_title: string;
  research_questions: string[];
  key_findings: string[];
  methodology: string | null;
  limitations: string[];
  key_contributions: string[];
  relevant_techniques: string[];
  cited_works: string[];
  future_work: string[];
  summary: string;
  tokens_used: number | null;
}

interface KnowledgePackagePayload {
  papers: ExtractedPaperKnowledge[];
}

function KnowledgeStatCard({
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

function Section({
  title,
  items,
  icon,
  emptyText = "No data",
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  emptyText?: string;
}) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      <h4 className="flex items-center gap-1.5 text-xs font-semibold text-text-muted uppercase tracking-wider">
        {icon}
        {title}
      </h4>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-1.5 text-sm text-text-primary">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent-default" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function KnowledgePaperCard({
  paper,
  index,
}: {
  paper: ExtractedPaperKnowledge;
  index: number;
}) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="space-y-4 pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-default/10 text-xs font-bold text-accent-default shrink-0">
                {index + 1}
              </span>
              <h3 className="text-sm font-semibold text-text-primary leading-snug">
                {paper.paper_title}
              </h3>
            </div>
          </div>
          {paper.tokens_used != null && (
            <span className="inline-flex items-center rounded-md border border-border bg-surface-card px-2 py-0.5 text-[10px] font-medium text-text-muted shrink-0">
              {paper.tokens_used} tokens
            </span>
          )}
        </div>

        {paper.summary && (
          <p className="text-sm text-text-secondary leading-relaxed">
            {paper.summary}
          </p>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <Section
            title="Research Questions"
            items={paper.research_questions}
            icon={<Target className="h-3 w-3" />}
          />
          <Section
            title="Key Findings"
            items={paper.key_findings}
            icon={<Lightbulb className="h-3 w-3" />}
          />
          <Section
            title="Key Contributions"
            items={paper.key_contributions}
            icon={<Sparkles className="h-3 w-3" />}
          />
          <Section
            title="Relevant Techniques"
            items={paper.relevant_techniques}
            icon={<ListTree className="h-3 w-3" />}
          />
          <Section
            title="Limitations"
            items={paper.limitations}
            icon={<TrendingUp className="h-3 w-3" />}
          />
          <Section
            title="Future Work"
            items={paper.future_work}
            icon={<BrainCircuit className="h-3 w-3" />}
          />
        </div>

        {paper.methodology && (
          <div className="space-y-1">
            <h4 className="flex items-center gap-1.5 text-xs font-semibold text-text-muted uppercase tracking-wider">
              <FileText className="h-3 w-3" />
              Methodology
            </h4>
            <p className="text-sm text-text-secondary">{paper.methodology}</p>
          </div>
        )}

        <Section
          title="Cited Works"
          items={paper.cited_works}
          icon={<Quote className="h-3 w-3" />}
        />
      </CardContent>
    </Card>
  );
}

export function WorkspaceKnowledgePage() {
  const { id } = useParams();
  const { data: artifacts, isLoading, isError } = useArtifacts(id);

  const knowledgeArtifacts = (artifacts ?? []).filter(
    (a) => a.artifact_type === "knowledge_package",
  );

  const latestKnowledge =
    knowledgeArtifacts.length > 0
      ? knowledgeArtifacts.sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime(),
        )[0]
      : null;

  const payload = latestKnowledge?.payload as KnowledgePackagePayload | null;

  const extractedPapers: ExtractedPaperKnowledge[] = Array.isArray(payload)
    ? (payload as unknown as ExtractedPaperKnowledge[])
    : payload?.papers ?? [];

  const totalTokens = extractedPapers.reduce(
    (sum, p) => sum + (p.tokens_used ?? 0),
    0,
  );

  const avgFindings = extractedPapers.length
    ? Math.round(
        extractedPapers.reduce((sum, p) => sum + p.key_findings.length, 0) /
          extractedPapers.length,
      )
    : 0;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Knowledge Extraction"
        description="LLM-extracted structured knowledge from retrieved papers"
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">
          Failed to load knowledge extraction data.
        </p>
      ) : extractedPapers.length > 0 ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KnowledgeStatCard
              icon={<BookOpen className="h-4 w-4" />}
              label="Papers Analysed"
              value={extractedPapers.length}
            />
            <KnowledgeStatCard
              icon={<Lightbulb className="h-4 w-4" />}
              label="Avg Findings per Paper"
              value={avgFindings}
            />
            <KnowledgeStatCard
              icon={<Sparkles className="h-4 w-4" />}
              label="Total Contributions"
              value={extractedPapers.reduce(
                (sum, p) => sum + p.key_contributions.length,
                0,
              )}
            />
            <KnowledgeStatCard
              icon={<BrainCircuit className="h-4 w-4" />}
              label="Total Tokens Used"
              value={totalTokens.toLocaleString()}
            />
          </div>

          {latestKnowledge && (
            <p className="text-xs text-text-muted">
              Extracted: {formatDateTime(latestKnowledge.created_at)}
            </p>
          )}

          <div className="space-y-3">
            {extractedPapers.map((paper, i) => (
              <KnowledgePaperCard key={paper.paper_id} paper={paper} index={i} />
            ))}
          </div>
        </>
      ) : (
        <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-border">
          <div className="flex flex-col items-center gap-2 text-sm text-text-muted">
            <BrainCircuit className="h-8 w-8" />
            <p>
              No knowledge extraction data available. Run the retrieval pipeline
              to generate extraction results.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
