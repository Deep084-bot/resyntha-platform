import type { ReactNode } from "react";
import { Bot, User } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Citation } from "@/types";

import { CitationChip } from "./CitationChip";
import { SuggestedQuestions } from "./SuggestedQuestions";

export interface ChatMessageModel {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  suggestedQuestions?: string[];
}

export interface ChatMessageProps {
  message: ChatMessageModel;
  onCitationClick: (citation: Citation) => void;
  onSuggestedQuestionClick: (question: string) => void;
  isStreaming?: boolean;
}

function renderInlineMarkdown(text: string): ReactNode[] {
  return text.split(/(`[^`]+`)/g).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={`${part}-${index}`}
          className="rounded bg-surface-hover px-1.5 py-0.5 text-[0.95em] text-text-primary"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

function renderMarkdown(content: string): ReactNode {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let paragraph: string[] = [];
  let listItems: string[] = [];
  let codeLines: string[] = [];
  let inCodeBlock = false;

  const flushParagraph = () => {
    if (!paragraph.length) return;
    const text = paragraph.join(" ").trim();
    if (text) {
      blocks.push(
        <p
          key={`p-${blocks.length}`}
          className="whitespace-pre-wrap leading-7 text-text-primary"
        >
          {renderInlineMarkdown(text)}
        </p>,
      );
    }
    paragraph = [];
  };

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(
      <ul
        key={`ul-${blocks.length}`}
        className="list-disc space-y-1 pl-5 text-text-primary"
      >
        {listItems.map((item, index) => (
          <li key={`${item}-${index}`} className="leading-7">
            {renderInlineMarkdown(item)}
          </li>
        ))}
      </ul>,
    );
    listItems = [];
  };

  const flushCode = () => {
    if (!codeLines.length) return;
    blocks.push(
      <pre
        key={`code-${blocks.length}`}
        className="overflow-x-auto rounded-xl bg-slate-950 px-4 py-3 text-sm text-slate-50"
      >
        <code>{codeLines.join("\n")}</code>
      </pre>,
    );
    codeLines = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        flushCode();
      } else {
        flushParagraph();
        flushList();
      }
      inCodeBlock = !inCodeBlock;
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      flushList();
      continue;
    }

    const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/);
    if (bulletMatch) {
      flushParagraph();
      const bulletText = bulletMatch[1];
      if (bulletText) {
        listItems.push(bulletText);
      }
      continue;
    }

    flushList();
    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();
  flushCode();

  if (blocks.length === 0) {
    return <p className="leading-7 text-text-primary">{content}</p>;
  }

  return <div className="space-y-4">{blocks}</div>;
}

export function ChatMessage({
  message,
  onCitationClick,
  onSuggestedQuestionClick,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <article
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start",
      )}
      aria-label={
        isUser ? "User message" : isStreaming ? "Assistant is typing" : "Assistant message"
      }
    >
      {isStreaming && (
        <div
          aria-live="polite"
          aria-atomic="false"
          className="sr-only"
        >
          {message.content}
        </div>
      )}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-default/10 text-accent-default">
          <Bot className="h-4 w-4" aria-hidden="true" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[min(48rem,100%)] space-y-3",
          isUser ? "items-end" : "items-start",
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-sm",
            isUser
              ? "bg-primary text-primary-foreground"
              : "border border-border bg-surface text-text-primary",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-7">{message.content}</p>
          ) : (
            renderMarkdown(message.content)
          )}
        </div>

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2" aria-label="Citations">
            {message.citations.map((citation, index) => (
              <CitationChip
                key={`${citation.paper_id ?? "citation"}-${index}`}
                citation={citation}
                onClick={onCitationClick}
              />
            ))}
          </div>
        )}

        {!isUser && message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Suggested follow-ups
            </p>
            <SuggestedQuestions
              questions={message.suggestedQuestions}
              onSelect={onSuggestedQuestionClick}
            />
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-text-primary/10 text-text-primary">
          <User className="h-4 w-4" aria-hidden="true" />
        </div>
      )}
    </article>
  );
}