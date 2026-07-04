import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InvestigationFilters } from "./InvestigationFilters";
import type { FilterState } from "../hooks";

afterEach(cleanup);

const defaultFilters: FilterState = {
  status: "all",
  sort: "newest",
  search: "",
};

describe("InvestigationFilters", () => {
  it("renders status filter with all options", () => {
    render(
      <InvestigationFilters filters={defaultFilters} onChange={() => {}} />,
    );
    const statusSelect = screen.getByLabelText(/filter by status/i);
    expect(statusSelect).toBeInTheDocument();
    expect(statusSelect).toHaveValue("all");
  });

  it("renders sort filter", () => {
    render(
      <InvestigationFilters filters={defaultFilters} onChange={() => {}} />,
    );
    const sortSelect = screen.getByLabelText(/sort order/i);
    expect(sortSelect).toBeInTheDocument();
    expect(sortSelect).toHaveValue("newest");
  });

  it("calls onChange when status filter changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <InvestigationFilters filters={defaultFilters} onChange={onChange} />,
    );

    await user.selectOptions(screen.getByLabelText(/filter by status/i), "completed");
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ status: "completed" }),
    );
  });

  it("calls onChange when sort changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <InvestigationFilters filters={defaultFilters} onChange={onChange} />,
    );

    await user.selectOptions(screen.getByLabelText(/sort order/i), "oldest");
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ sort: "oldest" }),
    );
  });
});
