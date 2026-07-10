# API Reference

All endpoints are prefixed with `/api/v1` (configurable via `API_V1_PREFIX`). Interactive docs available at `/api/v1/docs` (Swagger UI) and `/api/v1/redoc` (ReDoc) when `DOCS_ENABLED=true` and `REDOC_ENABLED=true`.

---

## Health

### GET `/health`
Full system health check. Returns status of all components.

**Response `200`**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 2.3},
    "redis": {"status": "healthy", "latency_ms": 1.1},
    "llm": {"status": "healthy"},
    "embeddings": {"status": "healthy", "dimension": 384},
    "worker": {"status": "available"}
  },
  "build_time": "2026-07-10T12:00:00Z",
  "git_commit": "abc1234"
}
```

### GET `/live`
Kubernetes-style liveness probe. Lightweight check that the server is running.

**Response `200`**
```json
{"status": "alive"}
```

### GET `/ready`
Kubernetes-style readiness probe. Checks that all dependencies are reachable.

**Response `200`**
```json
{"status": "ready"}
```

**Response `503`** — one or more dependencies unreachable
```json
{"status": "not_ready", "checks": {"database": {"status": "unhealthy", "error": "connection refused"}}}
```

### GET `/metrics/info`
Build metadata.

**Response `200`**
```json
{
  "application": "resyntha",
  "version": "0.1.0",
  "environment": "development",
  "git_commit": "abc1234",
  "build_time": "2026-07-10T12:00:00Z",
  "python_version": "3.12.4"
}
```

### GET `/metrics`
Prometheus-compatible metrics in exposition format.

**Response `200`** — Content-Type: `text/plain; version=0.0.4`
```
# HELP resyntha_backend_http_requests_total Total HTTP requests
# TYPE resyntha_backend_http_requests_total counter
resyntha_backend_http_requests_total{method="GET",path="/api/v1/health",status="200"} 42.0
# HELP resyntha_backend_http_request_duration_seconds HTTP request duration
# TYPE resyntha_backend_http_request_duration_seconds histogram
resyntha_backend_http_request_duration_seconds_bucket{method="GET",path="/api/v1/health",le="0.005"} 40.0
...
```

---

## Investigations

### POST `/investigations`
Create a research investigation.

**Request**
```json
{
  "title": "LLM Agents for Code Generation",
  "topic": "Large language model agents for automated code generation",
  "paper_limit": 15
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "title": "LLM Agents for Code Generation",
  "topic": "Large language model agents for automated code generation",
  "status": "draft",
  "created_at": "2026-07-10T12:00:00Z"
}
```

### GET `/investigations`
List all investigations.

**Query params**: `page` (default 1), `per_page` (default 20)

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "LLM Agents for Code Generation",
      "status": "completed",
      "paper_count": 15,
      "created_at": "2026-07-10T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### GET `/investigations/{investigation_id}`
Get investigation details.

**Response `200`**
```json
{
  "id": "uuid",
  "title": "LLM Agents for Code Generation",
  "topic": "Large language model agents for automated code generation",
  "status": "completed",
  "paper_limit": 15,
  "paper_count": 15,
  "created_at": "2026-07-10T12:00:00Z",
  "updated_at": "2026-07-10T14:00:00Z"
}
```

**Errors**: `404` — investigation not found

### DELETE `/investigations/{investigation_id}`
Delete an investigation and all associated data.

**Response `204`** — No content

**Errors**: `404` — investigation not found

### GET `/investigations/{investigation_id}/timeline`
Get investigation timeline events.

**Response `200`**
```json
[
  {
    "id": "uuid",
    "event_type": "pipeline_completed",
    "description": "Retrieval pipeline completed successfully",
    "timestamp": "2026-07-10T13:00:00Z"
  }
]
```

---

## Retrieval

### POST `/investigations/{investigation_id}/retrieve`
Trigger a retrieval pipeline execution. Runs asynchronously via ARQ worker.

**Request**
```json
{
  "query": "LLM agents code generation",
  "paper_limit": 15
}
```

**Response `202`**
```json
{
  "execution_id": "uuid",
  "status": "pending",
  "message": "Pipeline enqueued"
}
```

**Errors**: `404` — investigation not found

### GET `/investigations/{investigation_id}/papers`
List retrieved papers for an investigation.

**Query params**: `page` (default 1), `per_page` (default 20)

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "A Paper Title",
      "authors": ["Author A", "Author B"],
      "year": 2025,
      "venue": "Conference Name",
      "doi": "10.1234/example",
      "citation_count": 42,
      "source": "semantic_scholar",
      "status": "valid",
      "score": 85.5
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 20
}
```

**Errors**: `404` — investigation not found

---

## Executions

### POST `/investigations/{investigation_id}/executions`
Create a new execution for an investigation (manual trigger).

**Request**
```json
{
  "pipeline_name": "retrieval"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "investigation_id": "uuid",
  "pipeline_name": "retrieval",
  "status": "pending",
  "created_at": "2026-07-10T12:00:00Z"
}
```

### GET `/investigations/{investigation_id}/executions`
List executions for an investigation.

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "pipeline_name": "retrieval",
      "status": "completed",
      "created_at": "2026-07-10T12:00:00Z",
      "completed_at": "2026-07-10T12:05:00Z"
    }
  ],
  "total": 1
}
```

### GET `/executions/{execution_id}`
Get execution details.

**Response `200`**
```json
{
  "id": "uuid",
  "investigation_id": "uuid",
  "pipeline_name": "retrieval",
  "status": "completed",
  "result": "success",
  "created_at": "2026-07-10T12:00:00Z",
  "completed_at": "2026-07-10T12:05:00Z"
}
```

**Errors**: `404` — execution not found

### PATCH `/executions/{execution_id}`
Update execution status.

**Request**
```json
{
  "status": "running"
}
```

**Response `200`** — Updated execution

### GET `/executions/{execution_id}/stages`
List stage attempts for an execution.

**Response `200`**
```json
[
  {
    "stage_id": "retrieve",
    "status": "completed",
    "duration_ms": 3200,
    "error": null,
    "attempt": 1,
    "timestamp": "2026-07-10T12:00:00Z"
  }
]
```

---

## Artifacts

### POST `/investigations/{investigation_id}/artifacts`
Create an artifact.

**Request**
```json
{
  "type": "knowledge_package",
  "payload": {}
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "investigation_id": "uuid",
  "type": "knowledge_package",
  "status": "pending",
  "version": 1,
  "created_at": "2026-07-10T12:00:00Z"
}
```

### GET `/investigations/{investigation_id}/artifacts`
List artifacts for an investigation.

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "knowledge_package",
      "status": "ready",
      "version": 1,
      "created_at": "2026-07-10T12:00:00Z"
    }
  ],
  "total": 5
}
```

### GET `/artifacts/{artifact_id}`
Get single artifact with payload.

**Response `200`**
```json
{
  "id": "uuid",
  "investigation_id": "uuid",
  "type": "knowledge_package",
  "status": "ready",
  "version": 1,
  "payload": {},
  "created_at": "2026-07-10T12:00:00Z",
  "updated_at": "2026-07-10T12:05:00Z"
}
```

**Errors**: `404` — artifact not found

### PATCH `/artifacts/{artifact_id}`
Update artifact status or payload.

**Request**
```json
{
  "status": "ready",
  "payload": {}
}
```

**Response `200`** — Updated artifact

---

## Copilot

### GET `/investigations/{investigation_id}/copilot/messages`
List copilot conversation messages.

**Response `200`**
```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "What methodologies are used?",
      "created_at": "2026-07-10T12:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Based on the papers...",
      "citations": [{"paper_title": "...", "relevance": "..."}],
      "confidence": 0.85,
      "suggested_questions": ["..."],
      "created_at": "2026-07-10T12:01:00Z"
    }
  ]
}
```

### POST `/investigations/{investigation_id}/copilot/chat`
Send a message and get a response.

**Request**
```json
{
  "question": "What methodologies are most commonly used in this research area?"
}
```

**Response `200`**
```json
{
  "answer": "Based on the papers in this investigation...",
  "citations": [
    {"paper_title": "...", "paper_id": "uuid", "relevance": "Describes methodology X"}
  ],
  "confidence": 0.88,
  "reasoning": "The user asked about methodologies...",
  "suggested_questions": [
    "What are the key limitations?",
    "Which papers have the highest citation count?"
  ],
  "message_id": "uuid",
  "conversation_id": "uuid"
}
```

**Errors**: `404` — investigation not found

### POST `/investigations/{investigation_id}/copilot/chat/stream`
Stream a copilot response token-by-token.

**Request**
```json
{
  "question": "What methodologies are most commonly used?"
}
```

**Response** — Server-sent events (SSE) stream:
```
data: {"type": "token", "content": "Based"}
data: {"type": "token", "content": " on"}
data: {"type": "token", "content": " the"}
...
data: {"type": "done", "message_id": "uuid", "conversation_id": "uuid", "citations": [...], "confidence": 0.85}
```

**Errors** (streamed):
```
data: {"type": "error", "message": "Failed to retrieve investigation context."}
```

---

## Intelligence

### GET `/investigations/{investigation_id}/landscape`
Research landscape data.

**Response `200`** — Landscape with clusters, keywords, distributions

### GET `/investigations/{investigation_id}/landscape/markdown`
Landscape rendered as Markdown.

**Response `200`** — `text/markdown`

### GET `/investigations/{investigation_id}/landscape/json`
Landscape as raw JSON.

**Response `200`** — `application/json`

### GET `/investigations/{investigation_id}/overview`
Research overview.

**Response `200`** — Overview text and metrics

### GET `/investigations/{investigation_id}/institutions`
Institution analysis.

**Response `200`** — List of institutions with paper counts

### GET `/investigations/{investigation_id}/methodologies`
Methodology analysis.

**Response `200`** — Methodology clusters with frequency

### GET `/investigations/{investigation_id}/technologies`
Technology analysis.

**Response `200`** — Technology mentions with frequency

### GET `/investigations/{investigation_id}/datasets`
Dataset analysis.

**Response `200`** — Dataset references with frequency

### GET `/investigations/{investigation_id}/temporal`
Temporal analysis (publications over time).

**Response `200`** — Year-by-year publication counts

### GET `/investigations/{investigation_id}/collaborations`
Collaboration network analysis.

**Response `200`** — Collaboration frequency data

### GET `/investigations/{investigation_id}/graph`
Full research knowledge graph.

**Response `200`**
```json
{
  "nodes": [{"id": "...", "label": "...", "type": "paper|method|dataset|...", "group": "..."}],
  "edges": [{"source": "...", "target": "...", "relation": "...", "weight": 1}]
}
```

---

## Notes

### GET `/investigations/{investigation_id}/notes`
List notes.

**Response `200`** — Note list

### POST `/investigations/{investigation_id}/notes`
Create a note.

**Request**
```json
{
  "content": "Interesting finding about...",
  "source_type": "paper",
  "source_id": "uuid"
}
```

**Response `201`**

### GET `/investigations/{investigation_id}/notes/search`
Search notes.

**Query params**: `q` (search term)

**Response `200`** — Matching notes

### GET `/notes/{note_id}`
Get single note.

**Response `200`**

### PATCH `/notes/{note_id}`
Update note.

**Request**
```json
{
  "content": "Updated content"
}
```

**Response `200`**

### DELETE `/notes/{note_id}`
Delete note.

**Response `204`**

### GET `/notes/{note_id}/links`
List note links.

**Response `200`**

### POST `/notes/{note_id}/links`
Add a link to a note.

**Request**
```json
{
  "target_note_id": "uuid",
  "relationship": "related"
}
```

**Response `201`**

### DELETE `/links/{link_id}`
Delete a note link.

**Response `204`**

---

## Bookmarks

### GET `/investigations/{investigation_id}/bookmarks`
List bookmarks.

**Response `200`** — Bookmarked papers

### POST `/investigations/{investigation_id}/bookmarks`
Add bookmark.

**Request**
```json
{
  "paper_id": "uuid"
}
```

**Response `201`**

### DELETE `/bookmarks/{bookmark_id}`
Remove bookmark.

**Response `204`**

---

## Collections

### GET `/investigations/{investigation_id}/collections`
List collections.

**Response `200`** — Collection list

### POST `/investigations/{investigation_id}/collections`
Create collection.

**Request**
```json
{
  "name": "My Collection",
  "description": "Papers about..."
}
```

**Response `201`**

### GET `/collections/{collection_id}`
Get collection with papers.

**Response `200`**

### PATCH `/collections/{collection_id}`
Update collection.

**Response `200`**

### DELETE `/collections/{collection_id}`
Delete collection.

**Response `204`**

### POST `/collections/{collection_id}/papers`
Add paper to collection.

**Request**
```json
{
  "paper_id": "uuid"
}
```

**Response `200`**

### DELETE `/collections/{collection_id}/papers/{paper_id}`
Remove paper from collection.

**Response `204`**

---

## Reading Status

### GET `/investigations/{investigation_id}/papers/{paper_id}/reading-status`
Get reading status for a paper.

**Response `200`**
```json
{
  "status": "unread"
}
```

### PUT `/investigations/{investigation_id}/papers/{paper_id}/reading-status`
Set reading status.

**Request**
```json
{
  "status": "reading"
}
```

**Values**: `unread`, `reading`, `read`

**Response `200`**
```json
{
  "status": "reading"
}
```

---

## Root

### GET `/`
Application metadata.

**Response `200`**
```json
{
  "application": "resyntha",
  "version": "0.1.0",
  "environment": "development",
  "git_commit": "abc1234",
  "build_time": "2026-07-10T12:00:00Z",
  "status": "running"
}
```
