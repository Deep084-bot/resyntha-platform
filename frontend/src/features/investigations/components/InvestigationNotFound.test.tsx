import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { InvestigationNotFound } from "./InvestigationNotFound";

afterEach(cleanup);

describe("InvestigationNotFound", () => {
  it("renders not found message", () => {
    render(
      <MemoryRouter>
        <InvestigationNotFound />
      </MemoryRouter>,
    );
    expect(screen.getByText("Investigation not found")).toBeInTheDocument();
  });

  it("renders explanatory text", () => {
    render(
      <MemoryRouter>
        <InvestigationNotFound />
      </MemoryRouter>,
    );
    expect(
      screen.getByText(/doesn't exist or has been deleted/i),
    ).toBeInTheDocument();
  });

  it("renders a link back to dashboard", () => {
    render(
      <MemoryRouter>
        <InvestigationNotFound />
      </MemoryRouter>,
    );
    const link = screen.getByText("Back to Dashboard");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/");
  });

  it("has an alert role", () => {
    render(
      <MemoryRouter>
        <InvestigationNotFound />
      </MemoryRouter>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
