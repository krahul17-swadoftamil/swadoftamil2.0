// tailwind.config.js
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ================= APP BACKGROUNDS ================= */
        app: "var(--bg-app)",
        surface: "var(--bg-surface)",
        card: "var(--bg-card)",

        /* ================= TEXT ================= */
        text: "var(--text-primary)",
        muted: "var(--text-muted)",
        soft: "var(--text-soft)",

        /* ================= BRAND ================= */
        accent: "var(--accent)",
        "accent-strong": "var(--accent-strong)",

        /* ================= BORDERS & SHADOW ================= */
        border: "var(--border)",
      },
    },
  },
  plugins: [],
};
