import { create } from "zustand";

/**
 * Global UI state.
 *
 * Only values that are read by ≥ 2 unrelated components AND must
 * survive route changes belong here. Anything that fits in URL
 * state, a component's local state, or a server query lives
 * elsewhere.
 */

export type ThemeName = "dark" | "light";

interface UIState {
  /** Whether the sidebar is collapsed to icon-rail. */
  sidebarCollapsed: boolean;
  /** Active theme. */
  theme: ThemeName;
  /** Whether the command palette is open. */
  commandPaletteOpen: boolean;
  /** Whether the workspace inspector (right pane) is open. */
  inspectorOpen: boolean;
  /** Width in px of the workspace inspector. */
  inspectorWidth: number;

  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (t: ThemeName) => void;
  toggleTheme: () => void;
  setCommandPaletteOpen: (v: boolean) => void;
  setInspectorOpen: (v: boolean) => void;
  setInspectorWidth: (px: number) => void;
}

/* ── localStorage persistence for the persisted slice ──────────── */

const STORAGE_KEY = "resyntha:ui";
const PERSISTED_KEYS = ["sidebarCollapsed", "theme"] as const;
type PersistedKey = (typeof PERSISTED_KEYS)[number];

interface PersistedSlice {
  sidebarCollapsed: boolean;
  theme: ThemeName;
}

function readPersisted(): Partial<PersistedSlice> {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const out: Partial<PersistedSlice> = {};
    for (const k of PERSISTED_KEYS) {
      const v = parsed[k];
      if (k === "theme" && (v === "dark" || v === "light")) {
        out.theme = v;
      } else if (k === "sidebarCollapsed" && typeof v === "boolean") {
        out.sidebarCollapsed = v;
      }
    }
    return out;
  } catch {
    return {};
  }
}

function writePersisted(state: PersistedSlice): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Quota exceeded / private mode — fail silently.
  }
}

const initial = readPersisted();

export const useUIStore = create<UIState>((set, get) => ({
  sidebarCollapsed: initial.sidebarCollapsed ?? false,
  theme: initial.theme ?? "dark",
  commandPaletteOpen: false,
  inspectorOpen: false,
  inspectorWidth: 360,

  setSidebarCollapsed: (v) => {
    set({ sidebarCollapsed: v });
    writePersisted({ sidebarCollapsed: v, theme: get().theme });
  },
  toggleSidebar: () => {
    const next = !get().sidebarCollapsed;
    set({ sidebarCollapsed: next });
    writePersisted({ sidebarCollapsed: next, theme: get().theme });
  },

  setTheme: (t) => {
    set({ theme: t });
    writePersisted({ sidebarCollapsed: get().sidebarCollapsed, theme: t });
  },
  toggleTheme: () => {
    const next: ThemeName = get().theme === "dark" ? "light" : "dark";
    set({ theme: next });
    writePersisted({ sidebarCollapsed: get().sidebarCollapsed, theme: next });
  },

  setCommandPaletteOpen: (v) => set({ commandPaletteOpen: v }),
  setInspectorOpen: (v) => set({ inspectorOpen: v }),
  setInspectorWidth: (px) => set({ inspectorWidth: Math.max(240, Math.min(640, px)) }),
}));

// Re-export PersistedKey so internal call sites can stay typed
// without polluting the public surface.
export type { PersistedKey };
