import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { SortField } from "../hooks/usePaperFilters";
import { PaperSort } from "../components/PaperSort";

afterEach(cleanup);

function renderSort(
  value: SortField = "newest",
  onChange = vi.fn(),
) {
  return render(<PaperSort value={value} onChange={onChange} />);
}

describe("PaperSort", () => {
  it("renders sort label", () => {
    renderSort();
    expect(screen.getByText("Sort by")).toBeInTheDocument();
  });

  it("has the correct default value", () => {
    renderSort("newest");
    const select = screen.getByLabelText("Sort papers");
    expect(select).toHaveValue("newest");
  });

  it("shows all sort options", () => {
    renderSort();
    const select = screen.getByLabelText("Sort papers") as HTMLSelectElement;
    const options = Array.from(select.options).map((o) => o.value);
    expect(options).toEqual([
      "newest",
      "oldest",
      "most-cited",
      "alphabetical",
    ]);
  });

  it("calls onChange when a new option is selected", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderSort("newest", onChange);
    await user.selectOptions(
      screen.getByLabelText("Sort papers"),
      "oldest",
    );
    expect(onChange).toHaveBeenCalledWith("oldest");
  });

  it("displays the current sort value", () => {
    renderSort("most-cited");
    expect(screen.getByLabelText("Sort papers")).toHaveValue("most-cited");
  });

  it("has accessible label", () => {
    renderSort();
    expect(
      screen.getByLabelText("Sort papers"),
    ).toBeInTheDocument();
  });
});
