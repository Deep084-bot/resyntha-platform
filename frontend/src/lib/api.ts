import axios from "axios";

/**
 * Pre-configured Axios instance for the Resyntha API.
 *
 * Base URL defaults to the local backend dev server.
 * Interceptors handle token injection and error normalisation.
 */

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

/* ── Request interceptor — attach auth token ──────────────────── */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ── Response interceptor — normalise errors ──────────────────── */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const message =
        error.response?.data?.detail ??
        error.response?.data?.message ??
        error.message;
      return Promise.reject(new Error(message));
    }
    return Promise.reject(error);
  },
);

export default api;
