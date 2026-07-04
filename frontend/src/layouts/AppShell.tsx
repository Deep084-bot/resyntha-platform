import { useState } from "react";
import { Outlet } from "react-router-dom";
import {
  FileText,
  FlaskConical,
  LayoutDashboard,
  Search,
  Settings,
} from "lucide-react";

import { Sidebar, SidebarFooter, SidebarItem } from "@/components/navigation";
import { TopBar } from "@/components/navigation/TopBar";

export function AppShell() {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-surface-base text-text-primary">
      {/* Responsive sidebar */}
      <Sidebar
        mobileOpen={mobileSidebarOpen}
        onMobileClose={() => setMobileSidebarOpen(false)}
      >
        <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" end />
        <SidebarItem
          icon={Search}
          label="Investigations"
          to="/investigations"
        />
        <SidebarItem icon={FlaskConical} label="Research" to="/research" />
        <SidebarItem icon={FileText} label="Artifacts" to="/artifacts" />
        <SidebarFooter>
          <SidebarItem icon={Settings} label="Settings" to="/settings" />
        </SidebarFooter>
      </Sidebar>

      {/* Main area */}
      <div className="flex flex-1 flex-col min-w-0">
        <TopBar onMenuToggle={() => setMobileSidebarOpen((v) => !v)} />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
