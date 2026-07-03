import { beforeEach, describe, expect, it } from "vitest";

import { useNotificationsStore } from "./notifications";

describe("useNotificationsStore", () => {
  beforeEach(() => {
    useNotificationsStore.setState({ notifications: [] });
  });

  it("starts with an empty list", () => {
    expect(useNotificationsStore.getState().notifications).toEqual([]);
  });

  it("adds a notification", () => {
    const id = useNotificationsStore.getState().addNotification({
      type: "success",
      title: "Done",
    });

    const state = useNotificationsStore.getState();
    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0]!.id).toBe(id);
    expect(state.notifications[0]!.type).toBe("success");
    expect(state.notifications[0]!.title).toBe("Done");
    expect(state.notifications[0]!.duration).toBe(5000);
    expect(typeof state.notifications[0]!.createdAt).toBe("number");
  });

  it("adds a notification with optional fields", () => {
    useNotificationsStore.getState().addNotification({
      type: "error",
      title: "Failed",
      message: "Something went wrong",
      duration: 8000,
    });

    const n = useNotificationsStore.getState().notifications[0]!;
    expect(n.type).toBe("error");
    expect(n.message).toBe("Something went wrong");
    expect(n.duration).toBe(8000);
  });

  it("adds multiple notifications", () => {
    useNotificationsStore.getState().addNotification({ type: "info", title: "A" });
    useNotificationsStore.getState().addNotification({ type: "warning", title: "B" });

    expect(useNotificationsStore.getState().notifications).toHaveLength(2);
  });

  it("removes a notification by id", () => {
    const id = useNotificationsStore.getState().addNotification({
      type: "info",
      title: "To remove",
    });

    useNotificationsStore.getState().removeNotification(id);
    expect(useNotificationsStore.getState().notifications).toHaveLength(0);
  });

  it("does nothing when removing a non-existent id", () => {
    useNotificationsStore.getState().addNotification({ type: "info", title: "A" });
    useNotificationsStore.getState().removeNotification("non-existent");
    expect(useNotificationsStore.getState().notifications).toHaveLength(1);
  });

  it("clears all notifications", () => {
    useNotificationsStore.getState().addNotification({ type: "info", title: "A" });
    useNotificationsStore.getState().addNotification({ type: "info", title: "B" });

    useNotificationsStore.getState().clearAll();
    expect(useNotificationsStore.getState().notifications).toEqual([]);
  });

  it("generates unique ids", () => {
    const id1 = useNotificationsStore.getState().addNotification({ type: "info", title: "A" });
    const id2 = useNotificationsStore.getState().addNotification({ type: "info", title: "B" });

    expect(id1).not.toBe(id2);
  });
});
