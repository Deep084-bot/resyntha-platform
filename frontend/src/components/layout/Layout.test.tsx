import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { PageTitle } from "./PageTitle";
import { Workspace } from "./Workspace";
import { WorkspaceBody } from "./WorkspaceBody";
import { WorkspaceHeader } from "./WorkspaceHeader";

afterEach(cleanup);

describe("Workspace", () => {
  it("renders children", () => {
    render(<Workspace><span>content</span></Workspace>);
    expect(screen.getByText("content")).toBeInTheDocument();
  });
});

describe("WorkspaceHeader", () => {
  it("renders children", () => {
    render(<WorkspaceHeader><span>header</span></WorkspaceHeader>);
    expect(screen.getByText("header")).toBeInTheDocument();
  });
});

describe("WorkspaceBody", () => {
  it("renders children", () => {
    render(<WorkspaceBody><span>body</span></WorkspaceBody>);
    expect(screen.getByText("body")).toBeInTheDocument();
  });
});

describe("PageTitle", () => {
  it("renders text as h1 by default", () => {
    render(<PageTitle>Title</PageTitle>);
    const el = screen.getByText("Title");
    expect(el.tagName).toBe("H1");
  });

  it("renders with specified heading level", () => {
    render(<PageTitle as="h2">Subtitle</PageTitle>);
    const el = screen.getByText("Subtitle");
    expect(el.tagName).toBe("H2");
  });
});
