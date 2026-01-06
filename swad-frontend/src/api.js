/* ======================================================
   api.js — Swad of Tamil (OPTIMIZED)
   Session-based • Reload-safe • Django-aligned
   Features: Retry logic, deduplication, CSRF handling
====================================================== */

const RAW_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "/api";

export const API_BASE = RAW_BASE.replace(/\/$/, "");

// Request deduplication cache
const requestCache = new Map();
const REQUEST_CACHE_TTL = 5000; // 5 seconds

// CSRF token storage
let csrfToken = null;

/* ======================================================
   CSRF TOKEN MANAGEMENT
====================================================== */

async function getCsrfToken() {
  if (csrfToken) return csrfToken;

  try {
    // Try to get CSRF token from a cookie first
    const cookieToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];

    if (cookieToken) {
      csrfToken = cookieToken;
      return csrfToken;
    }

    // Fallback: Make a GET request to get the token
    const response = await fetch(`${API_BASE}/auth/csrf/`, {
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      csrfToken = data.csrfToken;
    }
  } catch (error) {
    console.warn('Failed to get CSRF token:', error);
  }

  return csrfToken;
}

/* ======================================================
   CORE REQUEST WITH RETRY & DEDUPLICATION
====================================================== */

async function request(endpoint, options = {}, retryCount = 0) {
  if (!endpoint.startsWith("/")) {
    throw new Error(`Endpoint must start with '/': ${endpoint}`);
  }

  const url = `${API_BASE}${endpoint}`;
  const cacheKey = `${options.method || 'GET'}-${url}-${JSON.stringify(options.body || {})}`;

  // Check cache for GET requests
  if ((options.method || 'GET') === 'GET' && requestCache.has(cacheKey)) {
    const cached = requestCache.get(cacheKey);
    if (Date.now() - cached.timestamp < REQUEST_CACHE_TTL) {
      return cached.data;
    } else {
      requestCache.delete(cacheKey);
    }
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const headers = {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    };

    // Add CSRF token for non-GET requests
    if ((options.method || 'GET') !== 'GET') {
      const token = await getCsrfToken();
      if (token) {
        headers['X-CSRFToken'] = token;
      }
    }

    const res = await fetch(url, {
      method: options.method || "GET",
      body: options.body,
      headers,
      credentials: "include", // 🔥 REQUIRED for Django sessions
      signal: controller.signal,
    });

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await res.json()
      : await res.text();

    if (!res.ok) {
      const error = new Error(extractError(data, res));
      error.status = res.status;
      error.data = data;

      // Retry logic for network errors and 5xx server errors
      if (retryCount < 2 && (res.status >= 500 || res.status === 0)) {
        console.warn(`Request failed, retrying (${retryCount + 1}/2):`, error.message);
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // Exponential backoff
        return request(endpoint, options, retryCount + 1);
      }

      throw error;
    }

    // Cache successful GET responses
    if ((options.method || 'GET') === 'GET') {
      requestCache.set(cacheKey, {
        data: data,
        timestamp: Date.now()
      });

      // Clean up old cache entries periodically
      if (requestCache.size > 50) {
        const now = Date.now();
        for (const [key, value] of requestCache.entries()) {
          if (now - value.timestamp > REQUEST_CACHE_TTL) {
            requestCache.delete(key);
          }
        }
      }
    }

    return data;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out (15s)");
    }

    // Retry network errors
    if (retryCount < 2 && (err.name === 'TypeError' || err.message.includes('fetch'))) {
      console.warn(`Network error, retrying (${retryCount + 1}/2):`, err.message);
      await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
      return request(endpoint, options, retryCount + 1);
    }

    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

/* ======================================================
   ERROR NORMALIZATION
====================================================== */

function extractError(data, res) {
  if (!data) return `${res.status} ${res.statusText}`;

  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  if (data.message) return data.message;

  if (typeof data === "object") {
    const first = Object.values(data)[0];
    if (Array.isArray(first)) return first[0];
    if (typeof first === "string") return first;
  }

  return `${res.status} ${res.statusText || "API Error"}`;
}

/* ======================================================
   QUERY PARAM HELPER
====================================================== */

function withParams(endpoint, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(
      ([, v]) => v !== undefined && v !== null && v !== ""
    )
  ).toString();

  return qs ? `${endpoint}?${qs}` : endpoint;
}

/* ======================================================
   PUBLIC API
====================================================== */

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

/* ======================================================
   DOMAIN HELPERS
====================================================== */

export function fetchCombos() {
  return api.get("/menu/combos/").catch(() => []);
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

export async function fetchSnackRegions() {
  try {
    return await api.get("/snacks/snacks/regions/");
  } catch {
    return [];
  }
}

export async function fetchMarketingOffers() {
  try {
    return await api.get("/menu/marketing-offers/");
  } catch {
    return [];
  }
}

export async function fetchStoreStatus() {
  try {
    return await api.get("/orders/store_status/");
  } catch {
    // Fallback to closed state
    return {
      is_open: false,
      accept_orders: false,
      kitchen_active: false,
      message: "Unable to check store status"
    };
  }
}

export function placeOrder(payload) {
  return api.post("/orders/", payload);
}
