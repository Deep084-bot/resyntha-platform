import { Bot } from "lucide-react";

import { SuggestedQuestions } from "./SuggestedQuestions";

export interface EmptyConversationProps {
  title: string;
  subtitle: string;
  suggestions: string[];
  onSelectSuggestion: (question: string) => void;
}

export function EmptyConversation({
  title,
  subtitle,
  suggestions,
  onSelectSuggestion,
}: EmptyConversationProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-border bg-surface-hover/40 px-6 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-default/10 text-accent-default">
        <Bot className="h-6 w-6" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-semibold text-text-primary">{title}</h3>
        <p className="max-w-lg text-sm text-text-muted">{subtitle}</p>
      </div>
      <SuggestedQuestions
        questions={suggestions}
        onSelect={onSelectSuggestion}
      />
    </div>
  );
}