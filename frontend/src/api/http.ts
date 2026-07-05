/**
 * The single Axios instance for the whole application.
 *
 * Components never import Axios; they go through `services/` which
 * go through this instance. Two interceptors sit on the instance:
 *
 *  1. Request — attaches the bearer token from the auth store.
 *  2. Response — normalises every error into an {@link AppError}.
 *
 * There is exactly one instance, exported as the default and as a
 * named `api` export for symmetry with service code.
 */

import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import { useAuthStore } from "@/stores/auth";
import { AppError, extractMessage, kindFromStatus } from "./errors";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  "http://localhost:8000/api/v1";

const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * The shared Axios instance.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT_MS,
  headers: { "Content-Type": "application/json" },
});

/* ── Request interceptor — bearer token from the auth store ────── */

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Read from the store, not localStorage, so the store remains the
  // single source of truth and tests can drive auth state directly.
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

/* ── Response interceptor — normalise to AppError ──────────────── */

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isCancel(error)) {
      return Promise.reject(
        new AppError("cancelled", "Request was cancelled"),
      );
    }

    if (error instanceof AxiosError) {
      if (error.code === "ECONNABORTED") {
        return Promise.reject(
          new AppError("timeout", "Request timed out"),
        );
      }
      if (!error.response) {
        return Promise.reject(
          new AppError("network", error.message || "Network error"),
        );
      }
      const status = error.response.status;
      const kind = kindFromStatus(status);
      const message = extractMessage(
        error.response.data,
        error.message || "Request failed",
      );
      return Promise.reject(
        new AppError(kind, message, status, error.response.data),
      );
    }

    return Promise.reject(error);
  },
);

/**
 * Re-export the instance under the canonical name.
 */
export { api };

/** Default export for `import api from "@/api/http"`. */
export default api;

/**
 * Type-safe helper for the rare case where a service needs to
 * pass a fully-typed request config. Just a passthrough that
 * returns its argument, but it gives the IDE a useful hint.
 */
export function requestConfig(config: AxiosRequestConfig): AxiosRequestConfig {
  return config;
}
