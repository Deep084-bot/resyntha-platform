import {
  createInvestigation,
  deleteInvestigation,
  fetchInvestigations,
} from "@/services/investigations";
import type { CreateInvestigationRequest, Investigation } from "@/types";

export async function listInvestigations(): Promise<Investigation[]> {
  return fetchInvestigations(0, 100);
}

export async function createNewInvestigation(
  body: CreateInvestigationRequest,
): Promise<Investigation> {
  return createInvestigation(body);
}

export async function removeInvestigation(id: string): Promise<void> {
  return deleteInvestigation(id);
}
