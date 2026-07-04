import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { JsonViewer } from "../components/JsonViewer";

afterEach(cleanup);

describe("JsonViewer", () => {
  it("renders string value", () => {
    render(<JsonViewer data="hello" />);
    expect(screen.getByText('"hello"')).toBeInTheDocument();
  });

  it("renders number value", () => {
    render(<JsonViewer data={42} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders boolean value", () => {
    render(<JsonViewer data={true} />);
    expect(screen.getByText("true")).toBeInTheDocument();
  });

  it("renders null value", () => {
    render(<JsonViewer data={null} />);
    expect(screen.getByText("null")).toBeInTheDocument();
  });

  it("renders object with key-value pairs", () => {
    const { container } = render(<JsonViewer data={{ name: "Alice", age: 30 }} />);
    // Check that keys and values appear in the rendered output
    expect(container.textContent).toContain("name");
    expect(container.textContent).toContain("Alice");
    expect(container.textContent).toContain("age");
    expect(container.textContent).toContain("30");
  });

  it("renders array with items", () => {
    const { container } = render(<JsonViewer data={["a", "b"]} />);
    expect(container.textContent).toContain("a");
    expect(container.textContent).toContain("b");
  });

  it("collapses deeply nested objects", () => {
    // Four levels of nesting; depth >= 3 auto-collapses, hiding deeper content
    const { container } = render(
      <JsonViewer data={{ l1: { l2: { l3: { l4: "deep" } } } }} />,
    );
    expect(container.textContent).toContain("l1");
    expect(container.textContent).toContain("l2");
    // l3 is at depth 3 and should show collapsed summary instead of children
    expect(container.textContent).toContain("1 item");
    expect(container.textContent).not.toContain("deep");
  });

  it("toggles collapse on click", async () => {
    const user = userEvent.setup();
    const { container } = render(<JsonViewer data={{ key: { inner: "value" } }} />);
    // Click the root-level collapse button (no keyName -> label is "Collapse object")
    const btn = screen.getByRole("button", { name: "Collapse object" });
    await user.click(btn);
    // The root is now collapsed, so children should not be visible
    expect(container.textContent).not.toContain("inner");
    // Click again to expand
    await user.click(btn);
    // Children are rendered again - "inner" key should be visible
    expect(container.textContent).toContain("inner");
  });
});
