import { useCallback, useEffect, useRef, useState } from "react";

import { SectionHeader } from "@/components/ui/section-header";
import type { Citation } from "@/types";

import { ChatInput } from "./ChatInput";
import { ChatMessage, type ChatMessageModel } from "./ChatMessage";
import { CopilotErrorState } from "./CopilotErrorState";
import { CopilotSkeleton } from "./CopilotSkeleton";
import { EmptyConversation } from "./EmptyConversation";


const DEFAULT_SUGGESTIONS = [
  "Summarize the research.",
  "What methodologies dominate?",
  "Compare the papers.",
  "What research gaps exist?",
  "Suggest future work.",
];

export interface CopilotChatProps {
  messages: ChatMessageModel[];
  isLoadingHistory: boolean;
  historyError: string | null;
  onRetryHistory: () => void;
  isSending: boolean;
  sendError: string | null;
  onRetrySend: () => void;
  onCancel?: () => void;
  onSend: (question: string) => void;
  onCitationClick: (citation: Citation) => void;
}

export function CopilotChat({
  messages,
  isLoadingHistory,
  historyError,
  onRetryHistory,
  isSending,
  sendError,
  onRetrySend,
  onCancel,
  onSend,
  onCitationClick,
}: CopilotChatProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messageEndRef.current?.scrollIntoView?.({
      behavior: "smooth",
      block: "end",
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending, scrollToBottom]);

  useEffect(() => {
    if (!isSending && !isLoadingHistory) {
      inputRef.current?.focus();
    }
  }, [isLoadingHistory, isSending]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    onSend(trimmed);
    setInput("");
  }, [input, isSending, onSend]);

  const handleSuggestionSelect = useCallback(
    (question: string) => {
      if (isSending) return;
      onSend(question);
      setInput("");
    },
    [isSending, onSend],
  );

  if (isLoadingHistory && messages.length === 0) {
    return <CopilotSkeleton />;
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Research Copilot"
        description="Ask questions about your completed investigation."
      />

      <div className="space-y-4">
        {historyError && messages.length === 0 ? (
          <CopilotErrorState
            title="We could not load your conversation."
            description={historyError}
            onRetry={onRetryHistory}
          />
        ) : messages.length === 0 ? (
          <EmptyConversation
            title="Research Copilot"
            subtitle="Ask questions about your completed investigation."
            suggestions={DEFAULT_SUGGESTIONS}
            onSelectSuggestion={handleSuggestionSelect}
          />
        ) : (
          <div
            className="space-y-5"
            role="log"
            aria-live="polite"
            aria-relevant="additions"
            aria-label="Copilot conversation"
          >
            {historyError && (
              <CopilotErrorState
                title="Conversation history could not be refreshed."
                description={historyError}
                onRetry={onRetryHistory}
              />
            )}
            {messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                isStreaming={index === messages.length - 1 && isSending && message.role === "assistant"}
                onCitationClick={onCitationClick}
                onSuggestedQuestionClick={handleSuggestionSelect}
              />
            ))}
          </div>
        )}

        {sendError && (
          <CopilotErrorState
            description={sendError}
            onRetry={onRetrySend}
          />
        )}

        <div ref={messageEndRef} />
      </div>

      <div className="space-y-3">
        {isSending && onCancel && (
          <div className="flex justify-center">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-medium text-text-muted hover:bg-surface-hover"
              aria-label="Stop generating"
            >
              Stop generating
            </button>
          </div>
        )}
        <ChatInput
          ref={inputRef}
          value={input}
          onChange={setInput}
          onSend={handleSend}
          isDisabled={isSending}
        />
      </div>
    </div>
  );
}
