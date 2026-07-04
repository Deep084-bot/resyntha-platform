import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileText, LayoutDashboard, Settings } from "lucide-react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { useUIStore } from "@/stores/ui";

import { Sidebar, SidebarFooter, SidebarItem, SidebarSection } from ".";

afterEach(() => {
  cleanup();
  useUIStore.setState({ sidebarCollapsed: false });
});

/* ── Helpers ─────────────────────────────────────────────────── */

function renderSidebar() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Sidebar>
        <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" end />
        <SidebarItem icon={FileText} label="Artifacts" to="/artifacts" />
        <SidebarSection label="Workspace">
          <SidebarItem icon={Settings} label="Settings" to="/settings" />
        </SidebarSection>
        <SidebarFooter>
          <SidebarItem icon={Settings} label="Settings" to="/settings" />
        </SidebarFooter>
      </Sidebar>
    </MemoryRouter>,
  );
}

/* ── Sidebar ─────────────────────────────────────────────────── */

describe("Sidebar", () => {
  it("renders brand name and logo", () => {
    renderSidebar();
    expect(screen.getAllByText("Resyntha")).toHaveLength(2);
  });

  it("renders nav item labels when expanded", () => {
    renderSidebar();
    expect(screen.getAllByText("Dashboard").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Artifacts").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Settings").length).toBeGreaterThanOrEqual(1);
  });

  it("highlights the active route", () => {
    render(
      <MemoryRouter initialEntries={["/artifacts"]}>
        <Sidebar>
          <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" end />
          <SidebarItem icon={FileText} label="Artifacts" to="/artifacts" />
        </Sidebar>
      </MemoryRouter>,
    );
    const artifactLinks = screen.getAllByText("Artifacts");
    for (const link of artifactLinks) {
      const anchor = link.closest("a");
      expect(anchor?.className).toContain("bg-sidebar-active");
    }
  });

  it("renders collapse toggle button", () => {
    renderSidebar();
    expect(
      screen.getByRole("button", { name: /collapse sidebar/i }),
    ).toBeInTheDocument();
  });

  it("toggles collapsed state on toggle click", async () => {
    const user = userEvent.setup();
    renderSidebar();

    const btn = screen.getByRole("button", { name: /collapse sidebar/i });
    await user.click(btn);

    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
  });

  it("renders mobile close button when mobileOpen is true", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Sidebar mobileOpen onMobileClose={() => {}}>
          <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" end />
        </Sidebar>
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("button", { name: /close navigation/i }),
    ).toBeInTheDocument();
  });
});

/* ── SidebarItem ─────────────────────────────────────────────── */

describe("SidebarItem", () => {
  it("renders icon and label when expanded", () => {
    render(
      <MemoryRouter>
        <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" />
      </MemoryRouter>,
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("hides label when sidebar is collapsed", () => {
    useUIStore.setState({ sidebarCollapsed: true });
    render(
      <MemoryRouter>
        <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" />
      </MemoryRouter>,
    );
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });
});

/* ── SidebarSection ──────────────────────────────────────────── */

describe("SidebarSection", () => {
  it("renders section label", () => {
    render(
      <MemoryRouter>
        <SidebarSection label="Workspace">
          <span>child</span>
        </SidebarSection>
      </MemoryRouter>,
    );
    expect(screen.getByText("Workspace")).toBeInTheDocument();
  });

  it("collapses children when section header is clicked", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <SidebarSection label="Workspace">
          <span>child</span>
        </SidebarSection>
      </MemoryRouter>,
    );
    expect(screen.getByText("child")).toBeInTheDocument();

    await user.click(screen.getByText("Workspace"));
    expect(screen.queryByText("child")).not.toBeInTheDocument();
  });
});

/* ── SidebarFooter ───────────────────────────────────────────── */

describe("SidebarFooter", () => {
  it("renders children", () => {
    render(
      <SidebarFooter>
        <span>footer item</span>
      </SidebarFooter>,
    );
    expect(screen.getByText("footer item")).toBeInTheDocument();
  });
});
