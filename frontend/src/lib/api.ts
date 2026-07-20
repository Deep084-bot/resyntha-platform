/**
 * Pre-configured Axios instance for the Resyntha API.
 *
 * Re-exports the canonical instance from `@/api/http` which provides
 * full AppError normalization, request cancellation support, and
 * bearer-token injection from the auth store.
 *
 * All service files import from this module.
 */

export { api as default } from "@/api/http";
