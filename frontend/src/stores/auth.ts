import { create } from "zustand";

/**
 * Minimal auth store.
 *
 * Holds the current auth token and user identity.
 * Real authentication logic will be added when
 * the auth module is implemented.
 */

interface AuthState {
  /** JWT access token or null when unauthenticated. */
  token: string | null;
  /** Cached user identifier. */
  user: string | null;
  /** Persist a new token and clear cached user. */
  setToken: (token: string | null) => void;
  /** Set the current user identifier. */
  setUser: (user: string | null) => void;
  /** Whether a token is present. */
  isAuthenticated: () => boolean;
  /** Clear all auth state (log out). */
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem("access_token"),
  user: null,

  setToken: (token) => {
    if (token) {
      localStorage.setItem("access_token", token);
    } else {
      localStorage.removeItem("access_token");
    }
    set({ token, user: null });
  },

  setUser: (user) => set({ user }),

  isAuthenticated: () => get().token !== null,

  logout: () => {
    localStorage.removeItem("access_token");
    set({ token: null, user: null });
  },
}));
