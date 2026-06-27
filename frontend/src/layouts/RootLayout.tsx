import { Outlet } from "react-router-dom";

import { Sidebar } from "@/layouts/Sidebar";

/**
 * Root application layout.
 *
 * Provides the persistent sidebar chrome.  Page-level headers
 * (workspace shell, simple page headers) are rendered by child
 * routes via <Outlet />.
 */
export function RootLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
