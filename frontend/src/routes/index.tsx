import { createBrowserRouter, Navigate, type RouteObject } from "react-router-dom";

import { AppShell } from "@/layouts/AppShell";
import { BlankLayout } from "@/layouts/BlankLayout";
import { DashboardPage } from "@/features/investigations/pages/DashboardPage";
import {
  ArtifactsPage,
  ExecutionsPage,
  LandscapePage,
  OverviewPage,
  PapersPage,
} from "@/features/investigations/pages";
import { CopilotPage } from "@/features/investigations/copilot/pages/CopilotPage";
import { GraphPage } from "@/features/investigations/graph/pages/GraphPage";
import { NotesPage } from "@/features/investigations/notes/pages/NotesPage";
import { InvestigationLayout } from "@/features/investigations/layout";
import { NotFoundPage } from "@/pages/NotFound";
import { PipelinePage } from "@/pages/Pipeline";
import { SettingsPage } from "@/pages/Settings";

const routes: RouteObject[] = [
  {
    // Protected routes — wrapped in AppShell (sidebar + top bar)
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      {
        path: "investigations/:id",
        element: <InvestigationLayout />,
        children: [
          { index: true, element: <OverviewPage /> },
          { path: "papers", element: <PapersPage /> },
          { path: "landscape", element: <LandscapePage /> },
          { path: "artifacts", element: <ArtifactsPage /> },
          { path: "executions", element: <ExecutionsPage /> },
          { path: "graph", element: <GraphPage /> },
          { path: "notes", element: <NotesPage /> },
          { path: "copilot", element: <CopilotPage /> },
        ],
      },
      // Sidebar nav items that don't have dedicated pages yet
      { path: "investigations", element: <Navigate to="/" replace /> },
      { path: "research", element: <Navigate to="/pipeline" replace /> },
      { path: "artifacts", element: <Navigate to="/" replace /> },
      { path: "pipeline", element: <PipelinePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    // Public routes — minimal blank layout (auth, landing, onboarding)
    element: <BlankLayout />,
    children: [
      // Future: login, signup, onboarding
    ],
  },
];

export const router = createBrowserRouter(routes);
