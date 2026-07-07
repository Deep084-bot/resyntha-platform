import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Citation } from "@/types";

import { CitationChip } from "../CitationChip";
import { ChatInput } from "../ChatInput";
import { ChatMessage } from "../ChatMessage";
import { EmptyConversation } from "../EmptyConversation";
import { SuggestedQuestions } from "../SuggestedQuestions";

afterEach(cleanup);

describe("CitationChip", () => {
  it("renders an interactive citation chip when a paper id exists", async () => {
    const citation: Citation = {
      paper_title: "Attention Is All You Need",
      paper_id: "paper-1",
      relevance: "Highly relevant",
    };
    const onClick = vi.fn();

    render(<CitationChip citation={citation} onClick={onClick} />);

    await userEvent.click(
      screen.getByRole("button", { name: /open citation for attention is all you need/i }),
    );

    expect(onClick).toHaveBeenCalledWith(citation);
  });

  it("renders a disabled chip when the paper id is missing", () => {
    render(
      <CitationChip
        citation={{ paper_title: "Unknown", paper_id: "", relevance: "" }}
      />,
    );

    expect(screen.getByText("Unknown")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("SuggestedQuestions", () => {
  it("calls the handler when a suggestion is clicked", async () => {
    const onSelect = vi.fn();

    render(
      <SuggestedQuestions
        questions={["Summarize the research.", "Suggest future work."]}
        onSelect={onSelect}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: /ask: summarize the research/i }),
    );

    expect(onSelect).toHaveBeenCalledWith("Summarize the research.");
  });
});

describe("ChatInput", () => {
  it("sends on Enter and keeps Shift+Enter as a newline", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    const onChange = vi.fn();

    render(
      <ChatInput value="Question" onChange={onChange} onSend={onSend} />,
    );

    const input = screen.getByRole("textbox", {
      name: /write a message to research copilot/i,
    });

    await user.click(input);
    await user.keyboard("{Enter}");
    expect(onSend).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("disables sending when the input is empty", () => {
    render(<ChatInput value="" onChange={vi.fn()} onSend={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: /send message/i }),
    ).toBeDisabled();
  });
});

describe("ChatMessage", () => {
  it("renders markdown, citations, and suggestions for assistant messages", async () => {
    const onCitationClick = vi.fn();
    const onSuggestedQuestionClick = vi.fn();

    render(
      <ChatMessage
        message={{
          id: "assistant-1",
          role: "assistant",
          content:
            "Summary paragraph.\n\n- First point\n- Second point\n\nUse `inline code` here.\n\n```\nconsole.log('hello');\n```",
          citations: [
            {
              paper_title: "Paper One",
              paper_id: "paper-1",
              relevance: "Relevant",
            },
          ],
          suggestedQuestions: ["What are the gaps?"],
        }}
        onCitationClick={onCitationClick}
        onSuggestedQuestionClick={onSuggestedQuestionClick}
      />,
    );

    expect(screen.getByText("Summary paragraph.")).toBeInTheDocument();
    expect(screen.getByText("First point")).toBeInTheDocument();
    expect(screen.getByText("Second point")).toBeInTheDocument();
    expect(screen.getByText("inline code")).toBeInTheDocument();
    expect(screen.getByText("console.log('hello');")).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: /open citation for paper one/i }),
    );
    expect(onCitationClick).toHaveBeenCalled();

    await userEvent.click(
      screen.getByRole("button", { name: /ask: what are the gaps\?/i }),
    );
    expect(onSuggestedQuestionClick).toHaveBeenCalledWith("What are the gaps?");
  });

  it("renders user messages on the right", () => {
    render(
      <ChatMessage
        message={{
          id: "user-1",
          role: "user",
          content: "What are the main findings?",
        }}
        onCitationClick={vi.fn()}
        onSuggestedQuestionClick={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("User message")).toBeInTheDocument();
    expect(
      screen.getByText("What are the main findings?"),
    ).toBeInTheDocument();
  });
});

describe("EmptyConversation", () => {
  it("renders the title, subtitle, and suggestion buttons", async () => {
    const onSelectSuggestion = vi.fn();

    render(
      <EmptyConversation
        title="Research Copilot"
        subtitle="Ask questions about your completed investigation."
        suggestions={["Summarize the research."]}
        onSelectSuggestion={onSelectSuggestion}
      />,
    );

    expect(screen.getByText("Research Copilot")).toBeInTheDocument();
    expect(
      screen.getByText("Ask questions about your completed investigation."),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: /ask: summarize the research\./i }),
    );
    expect(onSelectSuggestion).toHaveBeenCalledWith("Summarize the research.");
  });
});