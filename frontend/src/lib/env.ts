/**
 * Typed access to Vite environment variables.
 *
 * Centralising env access here means the rest of the code can
 * `import { env } from "@/lib/env"` instead of sprinkling
 * `import.meta.env.VITE_*` across the codebase. The default values
 * also let non-Vite environments (Vitest) run without throwing.
 */

const isTest = typeof import.meta !== "undefined" && Boolean(import.meta.env?.MODE);

function read(key: string, fallback?: string): string | undefined {
  // Vite injects `import.meta.env` at build time. In Vitest, that
  // object exists with VITE_* keys absent, so we fall through to
  // process.env for parity.
  const fromVite = (import.meta as ImportMeta).env?.[key];
  if (typeof fromVite === "string" && fromVite.length > 0) return fromVite;
  if (typeof process !== "undefined" && process.env?.[key]) {
    return process.env[key];
  }
  return fallback;
}

export interface AppEnv {
  /** API base URL including the version prefix. */
  apiUrl: string;
  /** True when running under Vitest. */
  isTest: boolean;
  /** True when NODE_ENV / MODE is development. */
  isDev: boolean;
  /** True when NODE_ENV / MODE is production. */
  isProd: boolean;
}

export const env: AppEnv = {
  apiUrl:
    read("VITE_API_URL", "http://localhost:8000/api/v1") ??
    "http://localhost:8000/api/v1",
  isTest: Boolean(isTest && (import.meta as ImportMeta).env?.MODE === "test"),
  isDev: (import.meta as ImportMeta).env?.MODE !== "production",
  isProd: (import.meta as ImportMeta).env?.MODE === "production",
};
