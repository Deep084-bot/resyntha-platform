export interface Note {
  id: string;
  investigation_id: string;
  title: string;
  content: string;
  tags: string[];
  source_type: string | null;
  source_id: string | null;
  source_context: string | null;
  created_at: string;
  updated_at: string;
}

export interface NoteCreateRequest {
  title: string;
  content: string;
  tags?: string[];
  source_type?: string | null;
  source_id?: string | null;
  source_context?: string | null;
}

export interface NoteUpdateRequest {
  title?: string;
  content?: string;
  tags?: string[];
}

export interface NoteLink {
  id: string;
  note_id: string;
  target_type: string;
  target_id: string;
  label: string | null;
  created_at: string;
}
