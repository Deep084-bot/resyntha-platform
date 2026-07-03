import { create } from "zustand";

export type NotificationType = "success" | "error" | "warning" | "info";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration: number;
  createdAt: number;
}

interface NotificationsState {
  notifications: Notification[];
  addNotification: (
    n: Omit<Notification, "id" | "createdAt" | "duration"> & { duration?: number },
  ) => string;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

let _nextId = 0;
const nextId = () => `notif_${++_nextId}`;

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  notifications: [],

  addNotification: (n) => {
    const id = nextId();
    const notif: Notification = {
      ...n,
      id,
      createdAt: Date.now(),
      duration: n.duration ?? 5000,
    };
    set({ notifications: [...get().notifications, notif] });
    return id;
  },

  removeNotification: (id) => {
    set({
      notifications: get().notifications.filter((n) => n.id !== id),
    });
  },

  clearAll: () => set({ notifications: [] }),
}));
