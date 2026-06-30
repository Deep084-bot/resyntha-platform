import api from "@/lib/api";
import type { ChatRequest, ChatResponse } from "@/types";

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
