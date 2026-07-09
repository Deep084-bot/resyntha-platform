export interface ReadingStatus {
  investigation_id: string;
  paper_id: string;
  status: "unread" | "reading" | "completed" | "skipped";
  updated_at: string;
}

export interface ReadingStatusSetRequest {
  status: string;
}
