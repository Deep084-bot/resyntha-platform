export interface Collection {
  id: string;
  investigation_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionCreateRequest {
  name: string;
  description?: string | null;
}

export interface CollectionPaperAddRequest {
  paper_id: string;
}
