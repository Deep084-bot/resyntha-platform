import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import { fetchCopilotHistory, sendChatMessage, streamChatMessage } from "@/services/copilot";
import type { ChatResponse, CopilotMessageDisplay, StreamingMessage } from "@/types";
import { queryKeys } from "@/types";

export function useCopilotChat(investigationId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<ChatResponse, Error, string>({
    mutationFn: (question: string) =>
      sendChatMessage(investigationId!, { question }),
    onMutate: async (question) => {
      if (!investigationId) return { previousHistory: [] as CopilotMessageDisplay[] };

      const historyKey = queryKeys.copilot.history(investigationId);
      await queryClient.cancelQueries({ queryKey: historyKey });

      const previousHistory =
        queryClient.getQueryData<CopilotMessageDisplay[]>(historyKey) ?? [];
      const optimisticMessage: CopilotMessageDisplay = {
        id: `pending-${Date.now()}`,
        role: "user",
        content: question,
        created_at: new Date().toISOString(),
      };

      queryClient.setQueryData<CopilotMessageDisplay[]>(historyKey, [
        ...previousHistory,
        optimisticMessage,
      ]);

      return { previousHistory };
    },
    onError: (_error, _question, context) => {
      if (!investigationId) return;

      const historyKey = queryKeys.copilot.history(investigationId);
      queryClient.setQueryData(historyKey, context?.previousHistory ?? []);
    },
    onSuccess: (result, question) => {
      if (!investigationId) return;

      const historyKey = queryKeys.copilot.history(investigationId);
      const currentHistory =
        queryClient.getQueryData<CopilotMessageDisplay[]>(historyKey) ?? [];
      const assistantMessage: CopilotMessageDisplay = {
        id: result.message_id,
        role: "assistant",
        content: result.answer,
        sources: result.citations,
        suggested_questions: result.suggested_questions,
        created_at: new Date().toISOString(),
      };

      const optimisticUserIndex = [...currentHistory]
        .map((message, index) => ({ message, index }))
        .reverse()
        .find(({ message }) => message.role === "user" && message.content === question);

      if (optimisticUserIndex) {
        const nextHistory = [...currentHistory];
        nextHistory.splice(optimisticUserIndex.index + 1, 0, assistantMessage);
        queryClient.setQueryData(historyKey, nextHistory);
      } else {
        queryClient.setQueryData<CopilotMessageDisplay[]>(historyKey, [
          ...currentHistory,
          assistantMessage,
        ]);
      }

      queryClient.invalidateQueries({ queryKey: historyKey });
    },
  });
}

export function useCopilotStream(investigationId: string | undefined) {
  const queryClient = useQueryClient();
  const abortRef = useRef<AbortController | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);

  const streamingContentRef = useRef("");

  const startStream = useCallback(
    async (question: string) => {
      if (!investigationId) return;

      setStreamError(null);
      setIsStreaming(true);
      streamingContentRef.current = "";

      const historyKey = queryKeys.copilot.history(investigationId);
      await queryClient.cancelQueries({ queryKey: historyKey });

      const previousHistory =
        queryClient.getQueryData<CopilotMessageDisplay[]>(historyKey) ?? [];

      const optimisticUser: CopilotMessageDisplay = {
        id: `pending-${Date.now()}`,
        role: "user",
        content: question,
        created_at: new Date().toISOString(),
      };

      queryClient.setQueryData<CopilotMessageDisplay[]>(historyKey, [
        ...previousHistory,
        optimisticUser,
      ]);

      const placeholderId = `streaming-${Date.now()}`;
      const placeholder: StreamingMessage = {
        id: placeholderId,
        role: "assistant",
        content: "",
        sources: [],
        suggested_questions: [],
        created_at: new Date().toISOString(),
      };
      setStreamingMessage(placeholder);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamChatMessage(
          investigationId,
          question,
          controller.signal,
          (token) => {
            streamingContentRef.current += token;
            setStreamingMessage((prev) =>
              prev ? { ...prev, content: prev.content + token } : null,
            );
          },
          (done) => {
            const finalMessage: CopilotMessageDisplay = {
              id: done.message_id,
              role: "assistant",
              content: streamingContentRef.current,
              sources: done.citations,
              suggested_questions: done.suggested_questions,
              created_at: new Date().toISOString(),
            };

            setStreamingMessage(null);
            setIsStreaming(false);

            const current =
              queryClient.getQueryData<CopilotMessageDisplay[]>(historyKey) ?? [];
            const idx = current.findIndex(
              (m) => m.id === optimisticUser.id,
            );
            if (idx !== -1) {
              const next = [...current];
              next.splice(idx + 1, 0, finalMessage);
              queryClient.setQueryData(historyKey, next);
            } else {
              queryClient.setQueryData<CopilotMessageDisplay[]>(historyKey, [
                ...current,
                finalMessage,
              ]);
            }

            queryClient.invalidateQueries({ queryKey: historyKey });
          },
          (errorMsg) => {
            setStreamError(errorMsg);
            setIsStreaming(false);
            setStreamingMessage(null);

            queryClient.setQueryData(historyKey, previousHistory);
          },
        );
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          setStreamingMessage(null);
          setIsStreaming(false);
          queryClient.setQueryData(historyKey, previousHistory);
          return;
        }

        const message =
          err instanceof Error ? err.message : "Stream request failed.";
        setStreamError(message);
        setIsStreaming(false);
        setStreamingMessage(null);
        queryClient.setQueryData(historyKey, previousHistory);
      }
    },
    [investigationId, queryClient],
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const retryStream = useCallback(
    (question: string) => {
      setStreamError(null);
      return startStream(question);
    },
    [startStream],
  );

  return {
    startStream,
    cancelStream,
    retryStream,
    streamingMessage,
    isStreaming,
    streamError,
  };
}

export function useCopilotHistory(investigationId: string | undefined) {
  return useQuery<CopilotMessageDisplay[]>({
    queryKey: queryKeys.copilot.history(investigationId!),
    queryFn: () => fetchCopilotHistory(investigationId!),
    enabled: !!investigationId,
    refetchOnWindowFocus: false,
    placeholderData: (previousData) => previousData,
  });
}
