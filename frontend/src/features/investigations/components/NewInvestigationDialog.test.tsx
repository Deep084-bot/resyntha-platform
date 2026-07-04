import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NewInvestigationDialog } from "./NewInvestigationDialog";

afterEach(cleanup);

describe("NewInvestigationDialog", () => {
  it("renders form fields", () => {
    render(
      <NewInvestigationDialog
        isPending={false}
        onSubmit={() => {}}
        onClose={() => {}}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /new investigation/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/research query/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/paper limit/i)).toBeInTheDocument();
  });

  it("shows validation errors when submitting empty form", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <NewInvestigationDialog
        isPending={false}
        onSubmit={onSubmit}
        onClose={() => {}}
      />,
    );

    await user.click(screen.getByRole("button", { name: /create investigation/i }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("Title is required")).toBeInTheDocument();
    expect(screen.getByText("Research query is required")).toBeInTheDocument();
  });

  it("calls onSubmit with form data when valid", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <NewInvestigationDialog
        isPending={false}
        onSubmit={onSubmit}
        onClose={() => {}}
      />,
    );

    await user.type(screen.getByLabelText(/title/i), "My Investigation");
    await user.type(
      screen.getByLabelText(/research query/i),
      "AI research topic",
    );
    await user.click(screen.getByRole("button", { name: /create investigation/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "My Investigation",
        topic: "AI research topic",
      }),
    );
  });

  it("shows error message when error prop is set", () => {
    render(
      <NewInvestigationDialog
        isPending={false}
        onSubmit={() => {}}
        onClose={() => {}}
        error="Something went wrong"
      />,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("calls onClose when cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <NewInvestigationDialog
        isPending={false}
        onSubmit={() => {}}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when close button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <NewInvestigationDialog
        isPending={false}
        onSubmit={() => {}}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: /close dialog/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("disables buttons when isPending is true", () => {
    render(
      <NewInvestigationDialog
        isPending={true}
        onSubmit={() => {}}
        onClose={() => {}}
      />,
    );

    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /creating/i }),
    ).toBeDisabled();
  });
});
