import { useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  BrainCircuit,
  FileText,
  Hash,
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

interface RankedItem {
  name: string;
  count: number;
  percentage: number;
}

interface CitationStats {
  total: number;
  average: number;
  median: number;
  max: number;
  min: number;
  total_with_data: number;
}

interface PublicationYearDistribution {
  years: Record<string, number>;
}

interface VenueDistribution {
  venues: Record<string, number>;
}

interface ResearchLandscape {
  paper_count: number;
  methodologies: RankedItem[];
  datasets: RankedItem[];
  evaluation_metrics: RankedItem[];
  research_domains: RankedItem[];
  tasks: RankedItem[];
  applications: RankedItem[];
  limitations: RankedItem[];
  future_work: RankedItem[];
  keywords: RankedItem[];
  novel_contributions: RankedItem[];
  top_authors: RankedItem[];
  publication_year_distribution: PublicationYearDistribution;
  venue_distribution: VenueDistribution;
  citation_statistics: CitationStats;
  clusters: Record<string, RankedItem[]>;
  generated_at: string;
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

/* ── Ranked List ──────────────────────────────────────────────── */

function RankedListCard({
  title,
  items,
  icon,
  maxItems = 8,
}: {
  title: string;
  items: RankedItem[];
  icon: React.ReactNode;
  maxItems?: number;
}) {
  if (items.length === 0) return null;
  const display = items.slice(0, maxItems);
  const maxCount = display[0]?.count ?? 1;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-semibold text-text-primary">
          {icon}
          {title}
          <span className="text-xs font-normal text-text-muted">
            ({items.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {display.map((item, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="w-5 text-right text-xs text-text-muted shrink-0">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-text-primary truncate">
                  {item.name}
                </span>
                <span className="text-xs text-text-muted shrink-0">
                  {item.count}
                </span>
              </div>
              <div className="mt-0.5 h-1.5 w-full rounded-full bg-surface-card overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent-default transition-all"
                  style={{ width: `${(item.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

/* ── Distribution Bar ─────────────────────────────────────────── */

function DistributionCard({
  title,
  distribution,
  icon,
  maxItems = 10,
}: {
  title: string;
  distribution: Record<string, number>;
  icon: React.ReactNode;
  maxItems?: number;
}) {
  const entries = Object.entries(distribution)
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxItems);

  if (entries.length === 0) return null;
  const maxCount = entries[0]![1];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-semibold text-text-primary">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {entries.map(([name, count], i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="w-5 text-right text-xs text-text-muted shrink-0">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-text-primary truncate">
                  {name}
                </span>
                <span className="text-xs text-text-muted shrink-0">
                  {count}
                </span>
              </div>
              <div className="mt-0.5 h-1.5 w-full rounded-full bg-surface-card overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent-default transition-all"
                  style={{ width: `${(count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

/* ── Cluster Section ──────────────────────────────────────────── */

function ClusterSection({
  clusters,
}: {
  clusters: Record<string, RankedItem[]>;
}) {
  const entries = Object.entries(clusters);
  if (entries.length === 0) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
        <BrainCircuit className="h-4 w-4" />
        Term Clusters
      </h3>
      {entries.map(([clusterName, items]) => (
        <RankedListCard
          key={clusterName}
          title={clusterName}
          items={items}
          icon={<ListTree className="h-4 w-4" />}
        />
      ))}
    </div>
  );
}

/* ── Main Page ────────────────────────────────────────────────── */

export function WorkspaceAnalysisPage() {
  const { id } = useParams();
  const { data: artifacts, isLoading, isError } = useArtifacts(id);

  const landscapeArtifact = useMemo(() => {
    const filtered = (artifacts ?? []).filter(
      (a) => a.artifact_type === "research_landscape",
    );
    return filtered.length > 0
      ? filtered.sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime(),
        )[0]
      : null;
  }, [artifacts]);

  const landscape = landscapeArtifact?.payload as ResearchLandscape | null;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Research Landscape"
        description="Cross-paper analysis of extracted knowledge"
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
        </div>
      ) : isError ? (
        <p className="text-sm text-destructive">
          Failed to load analysis data.
        </p>
      ) : landscape ? (
        <>
          {/* Stat cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={<BookOpen className="h-4 w-4" />}
              label="Papers Analyzed"
              value={landscape.paper_count}
            />
            <StatCard
              icon={<Hash className="h-4 w-4" />}
              label="Keywords"
              value={landscape.keywords.length}
            />
            <StatCard
              icon={<FileText className="h-4 w-4" />}
              label="Methodologies"
              value={landscape.methodologies.length}
            />
            <StatCard
              icon={<ListTree className="h-4 w-4" />}
              label="Datasets / Techniques"
              value={landscape.datasets.length}
            />
          </div>

          {landscape.generated_at && (
            <p className="text-xs text-text-muted">
              Analyzed: {formatDateTime(landscape.generated_at)}
            </p>
          )}

          {/* Publication year distribution */}
          {landscape.publication_year_distribution?.years &&
            Object.keys(landscape.publication_year_distribution.years)
              .length > 0 && (
              <DistributionCard
                title="Publication Timeline"
                distribution={
                  landscape.publication_year_distribution.years
                }
                icon={<TrendingUp className="h-4 w-4" />}
              />
            )}

          {/* Venue distribution */}
          {landscape.venue_distribution?.venues &&
            Object.keys(landscape.venue_distribution.venues)
              .length > 0 && (
              <DistributionCard
                title="Venues"
                distribution={landscape.venue_distribution.venues}
                icon={<FileText className="h-4 w-4" />}
              />
            )}

          {/* Citation stats */}
          {landscape.citation_statistics &&
            landscape.citation_statistics.total_with_data > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                    <Quote className="h-4 w-4" />
                    Citation Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div>
                      <p className="text-xs text-text-muted">Total</p>
                      <p className="text-lg font-bold text-text-primary">
                        {landscape.citation_statistics.total}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-text-muted">Average</p>
                      <p className="text-lg font-bold text-text-primary">
                        {landscape.citation_statistics.average.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-text-muted">Median</p>
                      <p className="text-lg font-bold text-text-primary">
                        {landscape.citation_statistics.median.toFixed(1)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

          {/* Ranked lists */}
          <div className="grid gap-4 sm:grid-cols-2">
            <RankedListCard
              title="Keywords"
              items={landscape.keywords}
              icon={<Hash className="h-4 w-4" />}
            />
            <RankedListCard
              title="Methodologies"
              items={landscape.methodologies}
              icon={<FileText className="h-4 w-4" />}
            />
            <RankedListCard
              title="Datasets / Techniques"
              items={landscape.datasets}
              icon={<ListTree className="h-4 w-4" />}
            />
            <RankedListCard
              title="Novel Contributions"
              items={landscape.novel_contributions}
              icon={<Sparkles className="h-4 w-4" />}
            />
            <RankedListCard
              title="Limitations"
              items={landscape.limitations}
              icon={<TrendingUp className="h-4 w-4" />}
            />
            <RankedListCard
              title="Future Work"
              items={landscape.future_work}
              icon={<Lightbulb className="h-4 w-4" />}
            />
            <RankedListCard
              title="Research Domains"
              items={landscape.research_domains}
              icon={<Target className="h-4 w-4" />}
            />
            <RankedListCard
              title="Applications"
              items={landscape.applications}
              icon={<BarChart3 className="h-4 w-4" />}
            />
          </div>

          {/* Clusters */}
          {landscape.clusters && (
            <ClusterSection clusters={landscape.clusters} />
          )}
        </>
      ) : (
        <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-border">
          <div className="flex flex-col items-center gap-2 text-sm text-text-muted">
            <BarChart3 className="h-8 w-8" />
            <p>
              No analysis available. Run the retrieval pipeline with
              knowledge extraction to generate a research landscape.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
