import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { Investigation } from "@/types";

import { InvestigationCard } from "./InvestigationCard";
import { LoadingState } from "./LoadingState";

export interface InvestigationListProps {
  investigations: Investigation[];
  isLoading: boolean;
  isError: boolean;
  search: string;
  onCreateNew: () => void;
  onDelete: (inv: Investigation) => void;
}

export function InvestigationList({
  investigations,
  isLoading,
  isError,
  search,
  onCreateNew,
  onDelete,
}: InvestigationListProps) {
  if (isLoading) {
    return <LoadingState count={4} />;
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-6 text-center">
        <p className="text-sm text-destructive">
          Failed to load investigations. Check your connection and try again.
        </p>
      </div>
    );
  }

  if (investigations.length === 0 && search) {
    return (
      <EmptyState
        title="No matching investigations"
        description={`No investigations match "${search}". Try a different search term.`}
      />
    );
  }

  if (investigations.length === 0) {
    return (
      <EmptyState
        title="No investigations yet"
        description="Create an investigation to begin collecting and analyzing research papers."
        action={
          <Button variant="outline" onClick={onCreateNew}>
            <Plus className="h-4 w-4" />
            New Investigation
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-2">
      {investigations.map((inv) => (
        <InvestigationCard
          key={inv.id}
          investigation={inv}
          onDelete={() => onDelete(inv)}
        />
      ))}
    </div>
  );
}
