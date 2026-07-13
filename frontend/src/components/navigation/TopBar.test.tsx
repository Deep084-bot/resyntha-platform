import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { TopBar } from "./TopBar";

afterEach(cleanup);

function renderTopBar(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <TopBar onMenuToggle={() => {}} />
    </MemoryRouter>,
  );
}

describe("TopBar", () => {
  it("renders search input", () => {
    renderTopBar();
    expect(
      screen.getByPlaceholderText(/search investigations/i),
    ).toBeInTheDocument();
  });

  it("renders breadcrumbs for root path showing Home", () => {
    renderTopBar("/");
    expect(screen.getByText("Home")).toBeInTheDocument();
  });

  it("renders breadcrumb segments for nested paths", () => {
    renderTopBar("/pipeline");
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Pipeline")).toBeInTheDocument();
  });

  it("renders menu toggle button for mobile", () => {
    renderTopBar();
    expect(
      screen.getByRole("button", { name: /toggle navigation menu/i }),
    ).toBeInTheDocument();
  });

  it("renders developer mode indicator", () => {
    renderTopBar();
    expect(screen.getByText("Developer Mode")).toBeInTheDocument();
  });
});

describe("Breadcrumbs", () => {
  it("shows known segment labels from mapping", () => {
    renderTopBar("/investigations");
    expect(screen.getByText("Investigations")).toBeInTheDocument();
  });

  it("capitalizes unknown segments", () => {
    renderTopBar("/unknown-route");
    expect(screen.getByText("Unknown-route")).toBeInTheDocument();
  });
});
