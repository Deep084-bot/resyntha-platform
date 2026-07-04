import { useState } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InvestigationSearch } from "./InvestigationSearch";

afterEach(cleanup);

function ControlledSearch() {
  const [value, setValue] = useState("");
  return (
    <div>
      <InvestigationSearch value={value} onChange={setValue} />
      <span data-testid="value">{value}</span>
    </div>
  );
}

describe("InvestigationSearch", () => {
  it("renders search input", () => {
    render(
      <InvestigationSearch value="" onChange={() => {}} />,
    );
    expect(
      screen.getByPlaceholderText(/search investigations/i),
    ).toBeInTheDocument();
  });

  it("updates value when user types", async () => {
    const user = userEvent.setup();
    render(<ControlledSearch />);

    const input = screen.getByRole("searchbox");
    await user.type(input, "test");

    expect(screen.getByTestId("value")).toHaveTextContent("test");
  });

  it("shows clear button when value is not empty", () => {
    render(<InvestigationSearch value="test" onChange={() => {}} />);
    expect(
      screen.getByRole("button", { name: /clear search/i }),
    ).toBeInTheDocument();
  });

  it("hides clear button when value is empty", () => {
    render(<InvestigationSearch value="" onChange={() => {}} />);
    expect(
      screen.queryByRole("button", { name: /clear search/i }),
    ).not.toBeInTheDocument();
  });

  it("clears search when clear button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<InvestigationSearch value="test" onChange={onChange} />);

    await user.click(screen.getByRole("button", { name: /clear search/i }));
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("renders searchbox with accessible role", () => {
    render(<InvestigationSearch value="" onChange={() => {}} />);
    expect(
      screen.getByRole("searchbox"),
    ).toBeInTheDocument();
  });
});
