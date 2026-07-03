/**
 * ID utilities.
 *
 * Framework-independent helpers for working with the UUIDs the
 * backend issues and with the short, user-visible ids the UI
 * uses to refer to entities in tables and breadcrumbs.
 */

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Loose UUID check — accepts both canonical 8-4-4-4-12 form and
 *  the versioned variants the backend can produce. */
export function isUuid(value: string | null | undefined): value is string {
  return typeof value === "string" && UUID_RE.test(value);
}

/** Short id for display: first 8 chars of a UUID, lowercased. */
export function shortId(id: string, length = 8): string {
  if (!id) return "";
  return id.slice(0, length).toLowerCase();
}

/** Stable id with a short prefix derived from the resource. */
export function prefixedId(resource: string, id: string): string {
  return `${resource.toLowerCase()}_${shortId(id, 8)}`;
}

/** Cheap, URL-safe random id for client-side placeholders. */
export function makeClientId(prefix = "id"): string {
  // Use crypto.getRandomValues when available; otherwise fall back
  // to Math.random (tests + very old browsers).
  if (typeof crypto !== "undefined" && "getRandomValues" in crypto) {
    const bytes = new Uint8Array(8);
    crypto.getRandomValues(bytes);
    let s = "";
    for (let i = 0; i < bytes.length; i += 1) {
      s += (bytes[i] ?? 0).toString(16).padStart(2, "0");
    }
    return `${prefix}_${s}`;
  }
  return `${prefix}_${Math.random().toString(16).slice(2, 18)}`;
}
