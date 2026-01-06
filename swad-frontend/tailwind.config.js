// tailwind.config.js
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // Heading fonts - elegant serif for brand feel
        'heading': ['Playfair Display', 'serif'],
        'heading-alt': ['Merriweather', 'serif'],
        
        // Body fonts - clean sans-serif for readability
        'body': ['Inter', 'sans-serif'],
        'body-alt': ['Poppins', 'sans-serif'],
        
        // System fallback
        'sans': ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
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
