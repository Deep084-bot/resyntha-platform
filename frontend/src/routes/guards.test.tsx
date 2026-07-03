import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

afterEach(cleanup);

import { useAuthStore } from "@/stores/auth";

import { RequireAnonymous, RequireAuth } from "./guards";

function renderGuard(Guard: typeof RequireAuth, fallback?: string) {
  return render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <Guard fallback={fallback}>
              <span>protected content</span>
            </Guard>
          }
        />
        <Route path="/login" element={<span>login page</span>} />
        <Route path="/" element={<span>home page</span>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAuth", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null });
  });

  it("renders children when authenticated", () => {
    useAuthStore.setState({ token: "valid-token" });
    renderGuard(RequireAuth);
    expect(screen.getByText("protected content")).toBeInTheDocument();
  });

  it("redirects when not authenticated", () => {
    renderGuard(RequireAuth, "/login");
    expect(screen.getByText("login page")).toBeInTheDocument();
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
  });

  it("redirects to default fallback /", () => {
    renderGuard(RequireAuth);
    expect(screen.getAllByText("home page").length).toBeGreaterThanOrEqual(1);
  });
});

describe("RequireAnonymous", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null });
  });

  it("renders children when not authenticated", () => {
    renderGuard(RequireAnonymous);
    expect(screen.getByText("protected content")).toBeInTheDocument();
  });

  it("redirects when authenticated", () => {
    useAuthStore.setState({ token: "valid-token" });
    renderGuard(RequireAnonymous, "/");
    expect(screen.getAllByText("home page").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
  });
});
