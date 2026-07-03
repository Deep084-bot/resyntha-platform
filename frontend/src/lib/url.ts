/**
 * URL helpers.
 *
 * Framework-independent query-string utilities. We avoid
 * `URLSearchParams` initialisation for trivial cases because the
 * shape `?a=1&b=2` is what we want to build, and going through
 * URLSearchParams is one extra allocation.
 */

/** Primitive value acceptable in a query string. */
export type QueryValue = string | number | boolean | null | undefined;

const isObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

/**
 * Build a query string from a record. Skips null/undefined/empty
 * string values so we never emit `?q=`.
 *
 * @example
 *   buildQuery({ q: "ai", page: 2, tags: ["a", "b"] })
 *   // → "q=ai&page=2&tags=a&tags=b"
 */
export function buildQuery(params: Record<string, QueryValue | QueryValue[]>): string {
  const parts: string[] = [];
  for (const key of Object.keys(params)) {
    const value = params[key];
    if (value === null || value === undefined) continue;
    if (Array.isArray(value)) {
      for (const v of value) {
        if (v === null || v === undefined) continue;
        parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(v))}`);
      }
    } else if (value !== "") {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
    }
  }
  return parts.join("&");
}

/** Compose a path with an optional query string. */
export function withQuery(path: string, params?: Record<string, QueryValue | QueryValue[]>): string {
  if (!params) return path;
  const qs = buildQuery(params);
  if (!qs) return path;
  return path.includes("?") ? `${path}&${qs}` : `${path}?${qs}`;
}

/**
 * Parse the query string of a URL or a `?...` suffix.
 * Returns an empty object for missing/empty input.
 */
export function parseQuery(search: string | URLSearchParams): Record<string, string> {
  const params =
    search instanceof URLSearchParams ? search : new URLSearchParams(search);
  const out: Record<string, string> = {};
  for (const [k, v] of params.entries()) out[k] = v;
  return out;
}

/**
 * Merge a record of params into an existing URL's search string.
 * Existing keys not in `overrides` are preserved; passing `null`
 * removes a key.
 */
export function mergeQuery(
  current: string | URLSearchParams,
  overrides: Record<string, QueryValue | null | undefined>,
): string {
  const params =
    current instanceof URLSearchParams
      ? new URLSearchParams(current)
      : new URLSearchParams(current);
  for (const [k, v] of Object.entries(overrides)) {
    if (v === null || v === undefined) params.delete(k);
    else params.set(k, String(v));
  }
  const s = params.toString();
  return s.length > 0 ? `?${s}` : "";
}

export const _testing = { isObject };
