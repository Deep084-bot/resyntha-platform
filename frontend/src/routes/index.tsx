import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { RootLayout } from "@/layouts/RootLayout";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { InvestigationsPage } from "@/pages/Investigations";
import { NotFoundPage } from "@/pages/NotFound";
import { PipelinePage } from "@/pages/Pipeline";
import { SettingsPage } from "@/pages/Settings";
import { WorkspaceAnalysisPage } from "@/pages/WorkspaceAnalysis";
import { WorkspaceArtifactsPage } from "@/pages/WorkspaceArtifacts";
import { WorkspaceExecutionsPage } from "@/pages/WorkspaceExecutions";
import { WorkspaceKnowledgePage } from "@/pages/WorkspaceKnowledge";
import { WorkspaceOverviewPage } from "@/pages/WorkspaceOverview";
import { WorkspacePapersPage } from "@/pages/WorkspacePapers";
import { WorkspaceResearchGapsPage } from "@/pages/WorkspaceResearchGaps";
import { WorkspaceTimelinePage } from "@/pages/WorkspaceTimeline";
import { WorkspaceValidationPage } from "@/pages/WorkspaceValidation";
import { WorkspaceCopilotPage } from "@/pages/WorkspaceCopilot";

const routes: RouteObject[] = [
  {
    path: "/",
    element: <RootLayout />,
    children: [
      { index: true, element: <InvestigationsPage /> },
      {
        path: "investigations/:id",
        element: <WorkspaceLayout />,
        children: [
          { index: true, element: <WorkspaceOverviewPage /> },
          { path: "timeline", element: <WorkspaceTimelinePage /> },
          { path: "artifacts", element: <WorkspaceArtifactsPage /> },
          { path: "papers", element: <WorkspacePapersPage /> },
          { path: "executions", element: <WorkspaceExecutionsPage /> },
          { path: "validation", element: <WorkspaceValidationPage /> },
          { path: "knowledge", element: <WorkspaceKnowledgePage /> },
          { path: "analysis", element: <WorkspaceAnalysisPage /> },
          { path: "gaps", element: <WorkspaceResearchGapsPage /> },
          { path: "copilot", element: <WorkspaceCopilotPage /> },
        ],
      },
      { path: "pipeline", element: <PipelinePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
