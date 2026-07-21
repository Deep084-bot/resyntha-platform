import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Outlet, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Investigation } from "@/types";
import type { StreamChunk } from "@/types";

vi.mock("@/services/copilot", () => {
  const streamChatMessage = vi.fn(
    (
      _investigationId: string,
      _question: string,
      signal: AbortSignal,
      _onToken: (token: string) => void,
      _onDone: (chunk: unknown) => void,
      _onError: (message: string) => void,
    ) =>
      new Promise<void>((_resolve, reject) => {
        if (signal.aborted) {
          reject(new DOMException("Aborted", "AbortError"));
          return;
        }
        signal.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        });
      }),
  );
  const fetchCopilotHistory = vi.fn().mockResolvedValue([]);
  return { fetchCopilotHistory, streamChatMessage };
});

import * as copilotModule from "@/services/copilot";

const fetchCopilotHistory = vi.mocked(copilotModule.fetchCopilotHistory);
const streamChatMessage = vi.mocked(copilotModule.streamChatMessage);

afterEach(() => {
  cleanup();
  fetchCopilotHistory.mockReset();
  streamChatMessage.mockClear();
});

beforeEach(() => {
  fetchCopilotHistory.mockResolvedValue([]);
});

const completedInvestigation: Investigation = {
  id: "inv-1",
  title: "Test Investigation",
  topic: "Machine Learning",
  status: "completed",
  paper_limit: 10,
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-20T14:30:00Z",
  metadata: null,
};

const lockedInvestigation: Investigation = {
  ...completedInvestigation,
  status: "analyzing",
};

function Parent({ investigation }: { investigation: Investigation }) {
  return <Outlet context={{ investigation }} />;
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

async function renderPage(investigation: Investigation, client: QueryClient) {
  const { CopilotPage } = await import("../CopilotPage");

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/investigations/inv-1/copilot"]}>
        <Routes>
          <Route
            path="/investigations/:id"
            element={<Parent investigation={investigation} />}
          >
            <Route path="copilot" element={<CopilotPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function makeDoneChunk(
  overrides?: Partial<StreamChunk & { type: "done" }>,
): StreamChunk & { type: "done" } {
  return {
    type: "done",
    message_id: "assistant-1",
    conversation_id: "conversation-1",
    citations: [
      { paper_title: "Paper One", paper_id: "paper-1", relevance: "Highly relevant" },
    ],
    suggested_questions: ["What methods dominate?"],
    confidence: 0.9,
    reasoning: "reasoning",
    ...overrides,
  };
}

async function waitForReady() {
  await waitFor(() => {
    expect(screen.getAllByText("Research Copilot").length).toBeGreaterThan(0);
  });
}

describe("CopilotPage", () => {
  it("shows the locked state before completion", async () => {
    const client = createQueryClient();
    await renderPage(lockedInvestigation, client);

    expect(screen.getByText("Research Copilot is locked")).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("shows the empty conversation state when history is empty", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);

    await waitForReady();

    expect(
      screen.getAllByText("Ask questions about your completed investigation.").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: /summarize the research/i }),
    ).toBeInTheDocument();
  });

  it("renders populated history from the backend", async () => {
    fetchCopilotHistory.mockResolvedValue([
      {
        id: "msg-1",
        role: "user" as const,
        content: "Summarize the research.",
        sources: [],
        suggested_questions: [],
        created_at: "2026-07-07T10:00:00+00:00",
      },
      {
        id: "msg-2",
        role: "assistant" as const,
        content: "Here is the summary.",
        sources: [
          { paper_title: "Paper One", paper_id: "paper-1", relevance: "Highly relevant" },
        ],
        suggested_questions: ["What methods dominate?"],
        created_at: "2026-07-07T10:00:05+00:00",
      },
    ]);

    const client = createQueryClient();
    await renderPage(completedInvestigation, client);

    expect(await screen.findByText("Summarize the research.")).toBeInTheDocument();
    expect(screen.getByText("Here is the summary.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /open citation for paper one/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /ask: what methods dominate\?/i }),
    ).toBeInTheDocument();
  });

  it("shows retry after history load failure", async () => {
    fetchCopilotHistory.mockRejectedValueOnce(new Error("backend unavailable"));

    const client = createQueryClient();
    await renderPage(completedInvestigation, client);

    expect(
      await screen.findByText("We could not load your conversation."),
    ).toBeInTheDocument();

    fetchCopilotHistory.mockResolvedValue([]);
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));

    await waitForReady();
  });

  it("sends a message which triggers streamChatMessage", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);
    await waitForReady();

    const user = userEvent.setup();
    await user.type(screen.getAllByRole("textbox")[0]!, "Test question.");
    await user.keyboard("{Enter}");

    await waitFor(() => {
      expect(streamChatMessage).toHaveBeenCalled();
    });
  });

  it("streams tokens into the conversation", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);
    await waitForReady();

    const user = userEvent.setup();
    await user.type(screen.getAllByRole("textbox")[0]!, "Summarize the research.");
    await user.keyboard("{Enter}");
    await waitFor(() => expect(streamChatMessage).toHaveBeenCalledTimes(1));

    const onToken = streamChatMessage.mock.calls[0]![3]!;
    const onDone = streamChatMessage.mock.calls[0]![4]!;

    onToken("Here ");
    onToken("is ");
    onToken("the ");
    onToken("summary.");

    // Simulate server persistence: refetch should include the saved message
    fetchCopilotHistory.mockResolvedValue([
      { id: "pending-1", role: "user" as const, content: "Summarize the research.", sources: [], suggested_questions: [], created_at: "" },
      { id: "assistant-1", role: "assistant" as const, content: "Here is the summary.", sources: [{ paper_title: "Paper One", paper_id: "paper-1", relevance: "Highly relevant" }], suggested_questions: ["What methods dominate?"], created_at: "" },
    ]);

    onDone(makeDoneChunk());

    await waitFor(() => {
      expect(screen.getByText("Here is the summary.")).toBeInTheDocument();
    });
  });

  it("shows retry when stream errors", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);
    await waitForReady();

    const user = userEvent.setup();
    await user.type(screen.getAllByRole("textbox")[0]!, "Summarize the research.");
    await user.keyboard("{Enter}");
    await waitFor(() => expect(streamChatMessage).toHaveBeenCalledTimes(1));

    const onError = streamChatMessage.mock.calls[0]![5]!;
    onError("backend error");

    await waitFor(() => {
      expect(screen.getByText("backend error")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("recovers after stream retry", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);
    await waitForReady();

    const user = userEvent.setup();
    await user.type(screen.getAllByRole("textbox")[0]!, "Summarize the research.");
    await user.keyboard("{Enter}");
    await waitFor(() => expect(streamChatMessage).toHaveBeenCalledTimes(1));

    const onError = streamChatMessage.mock.calls[0]![5]!;
    onError("backend error");

    await waitFor(() => {
      expect(screen.getByText("backend error")).toBeInTheDocument();
    });

    streamChatMessage.mockClear();

    await userEvent.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() => {
      expect(streamChatMessage).toHaveBeenCalledTimes(1);
    });

    const onToken2 = streamChatMessage.mock.calls[0]![3]!;
    const onDone2 = streamChatMessage.mock.calls[0]![4]!;
    onToken2("Retried ");
    onToken2("response.");

    // Simulate server persistence after retry
    fetchCopilotHistory.mockResolvedValue([
      { id: "pending-2", role: "user" as const, content: "Summarize the research.", sources: [], suggested_questions: [], created_at: "" },
      { id: "assistant-2", role: "assistant" as const, content: "Retried response.", sources: [], suggested_questions: [], created_at: "" },
    ]);

    onDone2(makeDoneChunk({ message_id: "assistant-2", citations: [], suggested_questions: [] }));

    await waitFor(() => {
      expect(screen.getByText("Retried response.")).toBeInTheDocument();
    });
  });

  it("cancels an in-progress stream", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);
    await waitForReady();

    const user = userEvent.setup();
    await user.type(screen.getAllByRole("textbox")[0]!, "Summarize the research.");
    await user.keyboard("{Enter}");
    await waitFor(() => expect(streamChatMessage).toHaveBeenCalledTimes(1));

    await userEvent.click(screen.getByRole("button", { name: /stop generating/i }));

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /stop generating/i })).not.toBeInTheDocument();
    });
    expect(screen.getByRole("textbox")).not.toBeDisabled();
  });

  it("shows streamed content for accessibility", async () => {
    const client = createQueryClient();
    await renderPage(completedInvestigation, client);
    await waitForReady();

    const user = userEvent.setup();
    await user.type(screen.getAllByRole("textbox")[0]!, "Summarize the research.");
    await user.keyboard("{Enter}");
    await waitFor(() => expect(streamChatMessage).toHaveBeenCalledTimes(1));

    const onToken = streamChatMessage.mock.calls[0]![3]!;
    onToken("Hello ");

    await waitFor(() => {
      expect(screen.getAllByText((_content, element) => element?.textContent === "Hello").length).toBeGreaterThan(0);
    });
  });
});
