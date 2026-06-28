import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createInvestigation as createInvestigationApi,
  deleteInvestigation as deleteInvestigationApi,
  fetchInvestigation,
  fetchInvestigations,
  fetchTimeline,
} from "@/services/investigations";
import type {
  CreateInvestigationRequest,
  Investigation,
  TimelineEvent,
} from "@/types";
import { queryKeys } from "@/types";

/* ── List ───────────────────────────────────────────────────── */

export function useInvestigations() {
  return useQuery<Investigation[]>({
    queryKey: queryKeys.investigations.all,
    queryFn: () => fetchInvestigations(),
  });
}

/* ── Detail ─────────────────────────────────────────────────── */

export function useInvestigation(id: string | undefined) {
  return useQuery<Investigation>({
    queryKey: queryKeys.investigations.detail(id!),
    queryFn: () => fetchInvestigation(id!),
    enabled: !!id,
  });
}

/* ── Create ─────────────────────────────────────────────────── */

export function useCreateInvestigation() {
  const qc = useQueryClient();
  return useMutation<Investigation, Error, CreateInvestigationRequest>({
    mutationFn: createInvestigationApi,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.investigations.all });
    },
  });
}

/* ── Delete ─────────────────────────────────────────────────── */

export function useDeleteInvestigation() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteInvestigationApi,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.investigations.all });
    },
  });
}

/* ── Timeline ───────────────────────────────────────────────── */

export function useTimeline(investigationId: string | undefined) {
  return useQuery<TimelineEvent[]>({
    queryKey: queryKeys.investigations.timeline(investigationId!),
    queryFn: () => fetchTimeline(investigationId!),
    enabled: !!investigationId,
  });
}
