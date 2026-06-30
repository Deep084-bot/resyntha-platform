import { useMutation } from "@tanstack/react-query";

import { sendChatMessage } from "@/services/copilot";
import type { ChatResponse } from "@/types";

export function useCopilotChat(investigationId: string | undefined) {
  return useMutation<ChatResponse, Error, string>({
    mutationFn: (question: string) =>
      sendChatMessage(investigationId!, { question }),
  });
}
