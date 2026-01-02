// src/utils/media.js

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function resolveMediaUrl(path) {
  if (!path) return null;

  // Accept either a string path or an object that may contain a URL field.
  if (typeof path === "object") {
    const maybe = path.url || path.path || path.image || path.image_url;
    if (!maybe) return null;
    path = maybe;
  }

  if (typeof path !== "string") return null;
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}
