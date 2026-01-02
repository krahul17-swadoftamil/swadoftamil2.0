// ======================================================
// Swad Admin — Stable Left Filter Sidebar
// Safe, minimal, no layout thrashing
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
  try {
    const BODY = document.body;
    BODY.classList.add("with-swad-sidebar");

    // Theme toggle support: persist and apply `swad-theme-light` class
    const THEME_KEY = 'swad:theme';
    function applyTheme(theme) {
      try {
        if (theme === 'light') BODY.classList.add('swad-theme-light'); else BODY.classList.remove('swad-theme-light');
        const btn = document.getElementById('swad-theme-toggle');
        if (btn) {
          btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
          btn.title = theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme';
        }
        localStorage.setItem(THEME_KEY, theme);
      } catch (e) { /* ignore */ }
    }

    try {
      let stored = localStorage.getItem(THEME_KEY);
      if (!stored) stored = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
      applyTheme(stored);
    } catch (e) { /* ignore */ }

    /* --------------------------------------------------
       Create sidebar
    -------------------------------------------------- */
    const sidebar = document.createElement("aside");
    sidebar.id = "swad-filter-sidebar";
    sidebar.innerHTML = `<div class="swad-filter-inner"></div>`;
    BODY.appendChild(sidebar);

    const inner = sidebar.querySelector(".swad-filter-inner");

    /* --------------------------------------------------
       Toggle button
    -------------------------------------------------- */
    const toggle = document.createElement("button");
    toggle.id = "swad-filter-toggle";
    toggle.type = "button";
    toggle.textContent = "Filters";
    BODY.appendChild(toggle);

    /* --------------------------------------------------
       Move Django changelist filters (ONE TIME)
    -------------------------------------------------- */
    const source =
      document.getElementById("changelist-filter") ||
      document.querySelector(".change-list .module");

    if (source) {
      const clone = source.cloneNode(true);

      // remove duplicate IDs
      clone.querySelectorAll("[id]").forEach(el => el.removeAttribute("id"));

      inner.appendChild(clone);
      source.style.display = "none";
    }

    /* --------------------------------------------------
       Toggle behavior
    -------------------------------------------------- */
    toggle.addEventListener("click", () => {
      BODY.classList.toggle("swad-sidebar-collapsed");

      if (window.innerWidth <= 900) {
        sidebar.classList.toggle("open");
      }
    });

    // Hook up header theme toggle if present
    const themeBtn = document.getElementById('swad-theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', (ev) => {
        ev.preventDefault();
        const current = BODY.classList.contains('swad-theme-light') ? 'light' : 'dark';
        applyTheme(current === 'light' ? 'dark' : 'light');
      });
    }

    /* --------------------------------------------------
       Mobile: close on outside click
    -------------------------------------------------- */
    document.addEventListener("click", (e) => {
      if (window.innerWidth > 900) return;
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });

    /* --------------------------------------------------
       Responsive reset
    -------------------------------------------------- */
    window.addEventListener("resize", () => {
      if (window.innerWidth > 900) {
        sidebar.classList.remove("open");
        BODY.classList.remove("swad-sidebar-collapsed");
      } else {
        BODY.classList.add("swad-sidebar-collapsed");
      }
    });

  } catch (err) {
    // never break admin
    console.warn("Swad admin sidebar failed safely", err);
  }
});
