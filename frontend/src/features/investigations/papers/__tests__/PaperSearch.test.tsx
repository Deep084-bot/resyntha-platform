import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PaperSearch } from "../components/PaperSearch";

afterEach(cleanup);

function renderSearch(
  value = "",
  onChange = vi.fn(),
  placeholder?: string,
) {
  return render(
    <PaperSearch
      value={value}
      onChange={onChange}
      placeholder={placeholder}
    />,
  );
}

describe("PaperSearch", () => {
  it("renders search input", () => {
    renderSearch();
    expect(
      screen.getByRole("searchbox"),
    ).toBeInTheDocument();
  });

  it("renders with placeholder text", () => {
    renderSearch("", vi.fn(), "Custom placeholder");
    expect(
      screen.getByPlaceholderText("Custom placeholder"),
    ).toBeInTheDocument();
  });

  it("calls onChange when user types", () => {
    const onChange = vi.fn();
    renderSearch("", onChange);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "deep" } });
    expect(onChange).toHaveBeenCalledWith("deep");
  });

  it("shows clear button when value is not empty", () => {
    renderSearch("deep learning");
    expect(
      screen.getByRole("button", { name: /clear search/i }),
    ).toBeInTheDocument();
  });

  it("does not show clear button when value is empty", () => {
    renderSearch("");
    expect(
      screen.queryByRole("button", { name: /clear search/i }),
    ).not.toBeInTheDocument();
  });

  it("calls onChange with empty string when clear button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderSearch("deep", onChange);
    await user.click(screen.getByRole("button", { name: /clear search/i }));
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("has searchbox ARIA role", () => {
    renderSearch();
    expect(screen.getByRole("searchbox")).toHaveAttribute(
      "aria-label",
      "Search papers",
    );
  });
});
