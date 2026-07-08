import { useCallback, useMemo, useRef } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { Bot } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { useCopilotHistory, useCopilotStream } from "@/hooks/useCopilot";
import { ROUTES } from "@/routes/paths";
import type { Citation, Investigation } from "@/types";

import { CopilotChat } from "../components/CopilotChat";

interface InvestigationOutletContext {
  investigation: Investigation;
}

interface CopilotChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  suggestedQuestions: string[];
}

export function CopilotPage() {
  const { investigation } = useOutletContext<InvestigationOutletContext>();
  const navigate = useNavigate();
  const historyQuery = useCopilotHistory(investigation.id);
  const {
    startStream,
    cancelStream,
    retryStream,
    streamingMessage,
    isStreaming,
    streamError,
  } = useCopilotStream(investigation.id);
  const lastQuestionRef = useRef("");

  const normalizedMessages = useMemo<CopilotChatMessage[]>(() => {
    const base = (historyQuery.data ?? []).map((message) => ({
      id: message.id,
      role: message.role as "user" | "assistant",
      content: message.content,
      citations: message.sources ?? [],
      suggestedQuestions: message.suggested_questions ?? [],
    }));

    if (streamingMessage) {
      base.push({
        id: streamingMessage.id,
        role: "assistant",
        content: streamingMessage.content,
        citations: streamingMessage.sources ?? [],
        suggestedQuestions: streamingMessage.suggested_questions ?? [],
      });
    }

    return base;
  }, [historyQuery.data, streamingMessage]);

  const handleSend = useCallback(
    (question: string) => {
      lastQuestionRef.current = question;
      startStream(question);
    },
    [startStream],
  );

  const handleRetrySend = useCallback(() => {
    if (!lastQuestionRef.current) return;
    retryStream(lastQuestionRef.current);
  }, [retryStream]);

  const handleCancel = useCallback(() => {
    cancelStream();
  }, [cancelStream]);

  const handleCitationClick = useCallback(
    (citation: Citation) => {
      if (!citation.paper_id) return;

      navigate(
        `${ROUTES.INVESTIGATION_PAPERS(investigation.id)}?paperId=${encodeURIComponent(citation.paper_id)}`,
      );
    },
    [investigation.id, navigate],
  );

  if (investigation.status !== "completed") {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-text-muted/10 text-text-muted">
            <Bot className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-text-primary">
              Research Copilot is locked
            </h2>
            <p className="max-w-lg text-sm text-text-muted">
              Complete an investigation to unlock AI Copilot.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <CopilotChat
      messages={normalizedMessages}
      isLoadingHistory={historyQuery.isLoading && !historyQuery.data}
      historyError={historyQuery.isError ? historyQuery.error.message : null}
      onRetryHistory={() => void historyQuery.refetch()}
      isSending={isStreaming}
      sendError={streamError}
      onRetrySend={handleRetrySend}
      onCancel={handleCancel}
      onSend={handleSend}
      onCitationClick={handleCitationClick}
    />
  );
}
