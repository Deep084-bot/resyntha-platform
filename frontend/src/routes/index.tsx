import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { RootLayout } from "@/layouts/RootLayout";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { InvestigationsPage } from "@/pages/Investigations";
import { NotFoundPage } from "@/pages/NotFound";
import { PipelinePage } from "@/pages/Pipeline";
import { SettingsPage } from "@/pages/Settings";
import { WorkspaceAnalysisPage } from "@/pages/WorkspaceAnalysis";
import { WorkspaceArtifactsPage } from "@/pages/WorkspaceArtifacts";
import { WorkspaceOverviewPage } from "@/pages/WorkspaceOverview";
import { WorkspacePapersPage } from "@/pages/WorkspacePapers";
import { WorkspaceTimelinePage } from "@/pages/WorkspaceTimeline";

const routes: RouteObject[] = [
  {
    path: "/",
    element: <RootLayout />,
    children: [
      { index: true, element: <InvestigationsPage /> },
      {
        path: "workspace/:id",
        element: <WorkspaceLayout />,
        children: [
          { index: true, element: <WorkspaceOverviewPage /> },
          { path: "timeline", element: <WorkspaceTimelinePage /> },
          { path: "artifacts", element: <WorkspaceArtifactsPage /> },
          { path: "papers", element: <WorkspacePapersPage /> },
          { path: "analysis", element: <WorkspaceAnalysisPage /> },
        ],
      },
      { path: "workspace", element: <WorkspaceOverviewPage /> },
      { path: "pipeline", element: <PipelinePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
