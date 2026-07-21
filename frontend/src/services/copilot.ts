import api from "@/lib/api";
import type {
  ChatRequest,
  ChatResponse,
  CopilotMessageDisplay,
  StreamChunk,
} from "@/types";

function normalizeHistoryResponse(data: unknown): CopilotMessageDisplay[] {
  if (!Array.isArray(data)) {
    throw new Error("Malformed copilot history response.");
  }

  return data.map((item) => {
    if (!item || typeof item !== "object") {
      throw new Error("Malformed copilot history response.");
    }

    const candidate = item as CopilotMessageDisplay;
    if (
      typeof candidate.id !== "string" ||
      typeof candidate.role !== "string" ||
      typeof candidate.content !== "string" ||
      typeof candidate.created_at !== "string"
    ) {
      throw new Error("Malformed copilot history response.");
    }

    return {
      id: candidate.id,
      role: candidate.role,
      content: candidate.content,
      sources: Array.isArray(candidate.sources) ? candidate.sources : [],
      suggested_questions: Array.isArray(candidate.suggested_questions)
        ? candidate.suggested_questions
        : [],
      created_at: candidate.created_at,
    };
  });
}

export async function sendChatMessage(
  investigationId: string,
  body: ChatRequest,
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>(
    `/investigations/${investigationId}/copilot/chat`,
    body,
  );
  return data;
}

export async function streamChatMessage(
  investigationId: string,
  question: string,
  signal: AbortSignal,
  onToken: (token: string) => void,
  onDone: (chunk: StreamChunk) => void,
  onError: (message: string) => void,
): Promise<void> {
  const baseUrl =
    import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

  const response = await fetch(
    `${baseUrl}/investigations/${investigationId}/copilot/chat/stream`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal,
    },
  );

  if (!response.ok) {
    await response.body?.cancel();
    throw new Error(`Stream request failed (${response.status})`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable.");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;

      try {
        const data: StreamChunk = JSON.parse(trimmed.slice(6));
        if (data.type === "token") {
          onToken(data.content);
        } else if (data.type === "done") {
          onDone(data);
        } else if (data.type === "error") {
          onError(data.message);
        }
      } catch {
        // skip malformed SSE lines
      }
    }
  }
}

export async function fetchCopilotHistory(
  investigationId: string,
): Promise<CopilotMessageDisplay[]> {
  const { data } = await api.get<unknown>(
    `/investigations/${investigationId}/copilot/messages`,
  );
  return normalizeHistoryResponse(data);
}
