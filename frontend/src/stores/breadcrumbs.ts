import { create } from "zustand";

interface BreadcrumbStore {
  labels: Record<string, string>;
  setLabel: (key: string, label: string) => void;
  clearLabel: (key: string) => void;
}

export const useBreadcrumbStore = create<BreadcrumbStore>((set) => ({
  labels: {},
  setLabel: (key, label) =>
    set((state) => ({ labels: { ...state.labels, [key]: label } })),
  clearLabel: (key) =>
    set((state) => {
      const next = { ...state.labels };
      delete next[key];
      return { labels: next };
    }),
}));
