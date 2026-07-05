import { useParams } from "react-router-dom";
import {
  BookOpen,
  Lightbulb,
  Building2,
  FlaskConical,
  Cpu,
  Database,
  BarChart3,
  GitMerge,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useLandscape } from "../hooks/useLandscape";
import { useInvestigation } from "@/hooks/useInvestigations";
import { useRunInvestigation } from "@/hooks/useExecutions";
import {
  SectionCard,
  LandscapeOverview,
  ObservationCard,
  InstitutionList,
  MethodologyList,
  TechnologyList,
  DatasetList,
  TemporalTimeline,
  CollaborationList,
  LandscapeSkeleton,
  LandscapeEmptyState,
  LandscapeErrorState,
} from "../components";

export function LandscapePage() {
  const { id } = useParams();
  const { data, isLoading, isError, error, isNotGenerated } = useLandscape(id);
  const { data: investigation } = useInvestigation(id);
  const runInvestigation = useRunInvestigation(id);

  const handleRunInvestigation = () => {
    const query = investigation?.topic ?? "";
    if (!query) return;
    runInvestigation.mutate({ query, paper_limit: investigation?.paper_limit ?? 10 });
  };

  if (isLoading) {
    return <LandscapeSkeleton />;
  }

  if (isNotGenerated) {
    return (
      <div
        className="flex h-64 flex-col items-center justify-center gap-4 rounded-md border border-dashed border-border"
        role="status"
      >
        <BookOpen className="h-10 w-10 text-text-muted" />
        <div className="text-center">
          <p className="text-sm font-medium text-text-primary">
            Landscape not yet available
          </p>
          <p className="mt-1 text-xs text-text-muted">
            Landscape will become available after the investigation pipeline finishes.
          </p>
          <Button
            onClick={handleRunInvestigation}
            disabled={runInvestigation.isPending}
            className="mt-4"
          >
            {runInvestigation.isPending ? (
              <>
                <Spinner size="sm" className="mr-2 border-t-white" />
                Running…
              </>
            ) : (
              "Run Investigation"
            )}
          </Button>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <LandscapeErrorState
        message={error?.message}
      />
    );
  }

  if (!data) {
    return <LandscapeEmptyState />;
  }

  const hasObservations = data.observations && data.observations.length > 0;
  const hasInstitutions = data.institutions && data.institutions.length > 0;
  const hasMethodologies =
    data.methodologies && data.methodologies.length > 0;
  const hasTechnologies = data.technologies && data.technologies.length > 0;
  const hasDatasets = data.datasets && data.datasets.length > 0;
  const hasTemporal = data.temporal_trends && data.temporal_trends.length > 0;
  const hasCollaborations =
    data.collaborations &&
    (data.collaborations.institution_collaborations.length > 0 ||
      data.collaborations.author_collaborations.length > 0);

  return (
    <div className="space-y-6" role="region" aria-label="Research landscape analysis">
      {/* Overview */}
      <SectionCard title="Overview" icon={<BookOpen className="h-4 w-4" />}>
        <LandscapeOverview data={data.overview} />
      </SectionCard>

      {/* Key Observations */}
      {hasObservations && (
        <SectionCard
          title="Key Observations"
          icon={<Lightbulb className="h-4 w-4" />}
        >
          <div className="space-y-3">
            {data.observations.map((obs, i) => (
              <ObservationCard key={`obs-${i}`} observation={obs} />
            ))}
          </div>
        </SectionCard>
      )}

      {/* Institutions */}
      {hasInstitutions && (
        <SectionCard
          title="Institutions"
          icon={<Building2 className="h-4 w-4" />}
        >
          <InstitutionList institutions={data.institutions} />
        </SectionCard>
      )}

      {/* Methodologies */}
      {hasMethodologies && (
        <SectionCard
          title="Methodologies"
          icon={<FlaskConical className="h-4 w-4" />}
        >
          <MethodologyList methodologies={data.methodologies} />
        </SectionCard>
      )}

      {/* Technologies */}
      {hasTechnologies && (
        <SectionCard
          title="Technologies"
          icon={<Cpu className="h-4 w-4" />}
        >
          <TechnologyList technologies={data.technologies} />
        </SectionCard>
      )}

      {/* Datasets */}
      {hasDatasets && (
        <SectionCard
          title="Datasets"
          icon={<Database className="h-4 w-4" />}
        >
          <DatasetList datasets={data.datasets} />
        </SectionCard>
      )}

      {/* Temporal Trends */}
      {hasTemporal && (
        <SectionCard
          title="Temporal Trends"
          icon={<BarChart3 className="h-4 w-4" />}
        >
          <TemporalTimeline trends={data.temporal_trends} />
        </SectionCard>
      )}

      {/* Collaborations */}
      {hasCollaborations && (
        <SectionCard
          title="Collaborations"
          icon={<GitMerge className="h-4 w-4" />}
        >
          <CollaborationList data={data.collaborations} />
        </SectionCard>
      )}
    </div>
  );
}
