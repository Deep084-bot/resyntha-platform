import { Button } from "@/components/ui/button";

export interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ questions, onSelect }: SuggestedQuestionsProps) {
  if (!questions.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((question) => (
        <Button
          key={question}
          type="button"
          variant="outline"
          size="sm"
          className="h-auto min-h-8 whitespace-normal break-words rounded-full border-border bg-surface px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary"
          onClick={() => onSelect(question)}
          aria-label={`Ask: ${question}`}
        >
          {question}
        </Button>
      ))}
    </div>
  );
}