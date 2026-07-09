import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GraphSearch } from "../components/GraphSearch";

afterEach(cleanup);

describe("GraphSearch", () => {
  it("renders the search input", () => {
    render(<GraphSearch value="" onChange={() => {}} />);
    expect(screen.getByPlaceholderText("Search nodes...")).toBeInTheDocument();
  });

  it("calls onChange when typing", () => {
    const onChange = vi.fn();
    render(<GraphSearch value="" onChange={onChange} />);
    const input = screen.getByPlaceholderText("Search nodes...");
    fireEvent.change(input, { target: { value: "Transformer" } });
    expect(onChange).toHaveBeenCalledWith("Transformer");
  });

  it("shows clear button when value is present", () => {
    render(<GraphSearch value="test" onChange={() => {}} />);
    expect(screen.getByLabelText("Clear search")).toBeInTheDocument();
  });

  it("does not show clear button when value is empty", () => {
    render(<GraphSearch value="" onChange={() => {}} />);
    expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();
  });

  it("calls onChange with empty string on clear", () => {
    const onChange = vi.fn();
    render(<GraphSearch value="test" onChange={onChange} />);
    fireEvent.click(screen.getByLabelText("Clear search"));
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("has accessible aria label", () => {
    render(<GraphSearch value="" onChange={() => {}} />);
    expect(screen.getByLabelText("Search graph nodes")).toBeInTheDocument();
  });
});
