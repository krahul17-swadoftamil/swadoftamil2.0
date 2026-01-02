/* ======================================================
   api.js — Swad of Tamil
   API-First • Mobile-Safe • ERP-Aligned
====================================================== */

const RAW_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api";

export const API_BASE = RAW_BASE.replace(/\/$/, "");

console.log("API_BASE →", API_BASE); // 🔥 DEBUG ONCE

async function request(endpoint, options = {}) {
  if (!endpoint.startsWith("/")) {
    throw new Error(`Endpoint must start with '/': ${endpoint}`);
  }

  const url = `${API_BASE}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const res = await fetch(url, {
      method: options.method || "GET",
      body: options.body,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    });

    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("application/json")
      ? await res.json()
      : await res.text();

    if (!res.ok) {
      throw new Error(normalizeError(data, res));
    }

    return data;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Request timeout (15s)");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

function normalizeError(data, res) {
  if (typeof data === "string" && data.trim()) return data;
  if (data?.detail) return data.detail;
  if (data?.message) return data.message;

  if (typeof data === "object") {
    const first = Object.values(data)[0];
    if (Array.isArray(first)) return first.join(" ");
    if (typeof first === "string") return first;
  }

  return `${res.status} ${res.statusText || "API Error"}`;
}

function withParams(endpoint, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(
      ([, v]) => v !== undefined && v !== null && v !== ""
    )
  ).toString();

  return qs ? `${endpoint}?${qs}` : endpoint;
}

export const api = {
  get(endpoint, params) {
    return request(withParams(endpoint, params));
  },
  post(endpoint, payload) {
    return request(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

/* ================= DOMAIN ================= */

export function fetchCombos() {
  return api.get("/menu/combos/");
}

export async function fetchPreparedItems() {
  const data = await api.get("/menu/prepared-items/");
  return Array.isArray(data?.results) ? data.results : data || [];
}

export async function fetchSnacks(params = {}) {
  try {
    return await api.get("/snacks/snacks/", params);
  } catch {
    return [];
  }
}

export function placeOrder(payload) {
  return api.post("/orders/", payload);
}
