import {
  forwardRef,
  type KeyboardEvent,
  type TextareaHTMLAttributes,
} from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ChatInputProps
  extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isDisabled?: boolean;
}

export const ChatInput = forwardRef<HTMLTextAreaElement, ChatInputProps>(
  ({ value, onChange, onSend, isDisabled = false, className, ...props }, ref) => {
    const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
        event.preventDefault();
        onSend();
      }
    };

    return (
      <div className="rounded-2xl border border-border bg-surface p-3 shadow-sm">
        <label className="sr-only" htmlFor="copilot-message-input">
          Write a message to Research Copilot
        </label>
        <textarea
          id="copilot-message-input"
          ref={ref}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          aria-label="Write a message to Research Copilot"
          placeholder="Ask a question about your completed investigation..."
          rows={3}
          className={cn(
            "w-full resize-none bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted",
            "disabled:cursor-not-allowed disabled:opacity-50",
            className,
          )}
          {...props}
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-xs text-text-muted">
            Press Enter to send, Shift+Enter for a new line.
          </p>
          <Button
            type="button"
            onClick={onSend}
            disabled={isDisabled || !value.trim()}
            aria-label="Send message"
          >
            Send
          </Button>
        </div>
      </div>
    );
  },
);

ChatInput.displayName = "ChatInput";