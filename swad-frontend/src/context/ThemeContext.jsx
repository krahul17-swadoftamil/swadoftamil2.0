import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

/* ======================================================
   THEME CONTEXT — ADVANCED
   Modes: light | dark | system
====================================================== */

const ThemeContext = createContext(null);

const STORAGE_KEY = "theme-preference";

/* ======================================================
   THEME PROVIDER
====================================================== */

export function ThemeProvider({ children }) {
  /**
   * themeMode = user's choice
   * "light" | "dark" | "system"
   */
  const [themeMode, setThemeMode] = useState("system");

  /**
   * systemTheme = actual OS theme
   * "light" | "dark"
   */
  const [systemTheme, setSystemTheme] = useState("dark");

  /* ================= SYSTEM THEME WATCH ================= */
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    const updateSystemTheme = () => {
      setSystemTheme(media.matches ? "dark" : "light");
    };

    updateSystemTheme();
    media.addEventListener("change", updateSystemTheme);

    return () =>
      media.removeEventListener("change", updateSystemTheme);
  }, []);

  /* ================= LOAD STORED PREF ================= */
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (stored === "light" || stored === "dark" || stored === "system") {
      setThemeMode(stored);
    }
  }, []);

  /* ================= RESOLVE FINAL THEME ================= */
  const resolvedTheme = useMemo(() => {
    return themeMode === "system" ? systemTheme : themeMode;
  }, [themeMode, systemTheme]);

  /* ================= APPLY TO DOM ================= */
  useEffect(() => {
    const root = document.documentElement;

    root.classList.remove("light", "dark");
    root.classList.add(resolvedTheme);
  }, [resolvedTheme]);

  /* ================= PERSIST ================= */
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, themeMode);
  }, [themeMode]);

  /* ================= CROSS-TAB SYNC ================= */
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        setThemeMode(e.newValue);
      }
    };

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  /* ================= ACTIONS ================= */
  const setLight = () => setThemeMode("light");
  const setDark = () => setThemeMode("dark");
  const setSystem = () => setThemeMode("system");

  const toggleTheme = () => {
    setThemeMode((prev) =>
      prev === "dark" ? "light" : "dark"
    );
  };

  /* ================= CONTEXT VALUE ================= */
  const value = {
    theme: resolvedTheme,      // actual applied theme
    themeMode,                 // user preference
    isSystem: themeMode === "system",
    setLight,
    setDark,
    setSystem,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

/* ======================================================
   SAFE HOOK
====================================================== */

export function useTheme() {
  const ctx = useContext(ThemeContext);

  if (!ctx) {
    throw new Error(
      "useTheme must be used within ThemeProvider"
    );
  }

  return ctx;
}
