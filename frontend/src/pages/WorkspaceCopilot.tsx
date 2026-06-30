import { useState, useRef, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Send, Bot, User, AlertCircle, Sparkles, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCopilotChat } from "@/hooks/useCopilot";
import type {
  ChatResponse,
  Citation,
  CopilotMessageDisplay,
} from "@/types";

function SourceCard({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface-card p-3 text-sm">
      <div className="mb-1 flex items-center gap-2">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-default/10 text-xs font-medium text-accent-default">
          {index + 1}
        </span>
        <span className="font-medium text-text-primary truncate">
          {citation.paper_title || "Unknown Source"}
        </span>
      </div>
      {citation.relevance && (
        <p className="text-xs text-text-muted line-clamp-2">
          {citation.relevance}
        </p>
      )}
    </div>
  );
}

function MessageBubble({
  message,
  onSuggestionClick,
}: {
  message: CopilotMessageDisplay;
  onSuggestionClick: (q: string) => void;
}) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-accent-default/20 text-accent-default"
            : "bg-primary/20 text-primary"
        }`}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      <div
        className={`max-w-[80%] space-y-2 ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-accent-default text-white"
              : "bg-surface-card border border-border text-text-primary"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.sources.map((citation, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 rounded-full bg-accent-default/10 px-2 py-0.5 text-xs text-accent-default"
              >
                <Sparkles className="h-3 w-3" />
                {citation.paper_title?.slice(0, 40) ||
                  `Source ${i + 1}`}
              </span>
            ))}
          </div>
        )}

        {!isUser &&
          message.suggested_questions &&
          message.suggested_questions.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-text-muted">Suggested follow-ups:</p>
              <div className="flex flex-wrap gap-1.5">
                {message.suggested_questions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => onSuggestionClick(q)}
                    className="rounded-full border border-border bg-surface-base px-3 py-1 text-xs text-text-secondary transition-colors hover:bg-surface-card hover:text-text-primary"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
      </div>
    </div>
  );
}

export function WorkspaceCopilotPage() {
  const { id } = useParams();
  const chatMutation = useCopilotChat(id);

  const [messages, setMessages] = useState<CopilotMessageDisplay[]>([]);
  const [input, setInput] = useState("");
  const [selectedCitations, setSelectedCitations] = useState<Citation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = useCallback(
    async (question: string) => {
      if (!question.trim() || !id) return;

      const userMsg: CopilotMessageDisplay = {
        id: `user-${Date.now()}`,
        role: "user",
        content: question.trim(),
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");

      try {
        const result: ChatResponse = await chatMutation.mutateAsync(
          question.trim(),
        );

        const assistantMsg: CopilotMessageDisplay = {
          id: result.message_id,
          role: "assistant",
          content: result.answer,
          sources: result.citations,
          suggested_questions: result.suggested_questions,
          created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
        setSelectedCitations(result.citations);
      } catch {
        const errorMsg: CopilotMessageDisplay = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            "Sorry, I encountered an error processing your question. Please try again.",
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    },
    [id, chatMutation],
  );

  const handleSuggestionClick = useCallback(
    (question: string) => {
      handleSend(question);
    },
    [handleSend],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend(input);
      }
    },
    [handleSend, input],
  );

  return (
    <div className="flex h-full gap-0">
      {/* Chat Panel */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-default/10">
                <Bot className="h-6 w-6 text-accent-default" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-text-primary">
                  Research Copilot
                </h3>
                <p className="mt-1 text-xs text-text-muted max-w-xs">
                  Ask questions about the papers, findings, and analysis
                  in this investigation.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  onSuggestionClick={handleSuggestionClick}
                />
              ))}
            </div>
          )}

          {chatMutation.isPending && (
            <div className="mt-4 flex items-center gap-2 text-sm text-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about this investigation..."
              disabled={chatMutation.isPending}
              className="flex-1 rounded-lg border border-border bg-surface-card px-4 py-2.5 text-sm text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent-default disabled:opacity-50"
            />
            <Button
              onClick={() => handleSend(input)}
              disabled={!input.trim() || chatMutation.isPending}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Sources Panel */}
      <div className="hidden w-72 shrink-0 border-l border-border p-4 lg:block">
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-muted">
          Sources
        </h4>
        {selectedCitations.length > 0 ? (
          <div className="space-y-2">
            {selectedCitations.map((citation, i) => (
              <SourceCard key={i} citation={citation} index={i} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-8 text-center text-xs text-text-muted">
            <AlertCircle className="h-5 w-5" />
            <p>
              Sources cited in the assistant's response will appear here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
