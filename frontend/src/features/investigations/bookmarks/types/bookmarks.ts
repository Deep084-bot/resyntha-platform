export interface Bookmark {
  id: string;
  investigation_id: string;
  paper_id: string;
  notes: string | null;
  created_at: string;
}

export interface BookmarkCreateRequest {
  paper_id: string;
  notes?: string | null;
}
