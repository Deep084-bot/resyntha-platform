import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { InstitutionList } from "../components/InstitutionList";
import type { Institution } from "../types";

afterEach(cleanup);

const mockInstitutions: Institution[] = [
  { name: "MIT", type: "University", paper_count: 45, author_count: 120 },
  { name: "Google Research", type: "Industry", paper_count: 38, author_count: 95 },
];

describe("InstitutionList", () => {
  it("renders institution names", () => {
    render(<InstitutionList institutions={mockInstitutions} />);
    expect(screen.getByText("MIT")).toBeInTheDocument();
    expect(screen.getByText("Google Research")).toBeInTheDocument();
  });

  it("renders institution types", () => {
    render(<InstitutionList institutions={mockInstitutions} />);
    expect(screen.getByText("University")).toBeInTheDocument();
    expect(screen.getByText("Industry")).toBeInTheDocument();
  });

  it("renders paper and author counts", () => {
    render(<InstitutionList institutions={mockInstitutions} />);
    expect(screen.getByText("45")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("38")).toBeInTheDocument();
    expect(screen.getByText("95")).toBeInTheDocument();
  });

  it("shows empty state when no institutions", () => {
    render(<InstitutionList institutions={[]} />);
    expect(
      screen.getByText("No institution data available."),
    ).toBeInTheDocument();
  });
});
