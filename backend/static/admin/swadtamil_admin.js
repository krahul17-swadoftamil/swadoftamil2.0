// ======================================================
// SWAD ADMIN — CHANGE LIST FILTER SIDEBAR
// FINAL • STABLE • DJANGO SAFE • MODAL SAFE
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
  try {
    /* --------------------------------------------------
       ONLY RUN ON CHANGE LIST PAGES
    -------------------------------------------------- */
    const filterSource =
      document.getElementById("changelist-filter") ||
      document.querySelector(".change-list .module");

    if (!filterSource) return; // Never run on change_form / login / OTP pages

    /* --------------------------------------------------
       CONSTANTS
    -------------------------------------------------- */
    const SIDEBAR_ID = "swad-filter-sidebar";
    const TOGGLE_ID = "swad-filter-toggle";
    const LS_COLLAPSED = "swad:sidebar-collapsed";
    const LS_OPEN = "swad:sidebar-open";

    /* --------------------------------------------------
       CREATE SIDEBAR (ONCE)
    -------------------------------------------------- */
    let sidebar = document.getElementById(SIDEBAR_ID);
    if (!sidebar) {
      sidebar = document.createElement("aside");
      sidebar.id = SIDEBAR_ID;
      sidebar.innerHTML = `<div class="swad-filter-inner" tabindex="-1"></div>`;
      document.body.appendChild(sidebar);
    }

    /* --------------------------------------------------
       CREATE TOGGLE (ONCE)
    -------------------------------------------------- */
    let toggle = document.getElementById(TOGGLE_ID);
    if (!toggle) {
      toggle = document.createElement("button");
      toggle.id = TOGGLE_ID;
      toggle.type = "button";
      toggle.textContent = "Filters";
      document.body.appendChild(toggle);
    }

    document.body.classList.add("with-swad-sidebar");

    /* --------------------------------------------------
       MOVE FILTERS (NO CLONE — PRESERVE EVENTS)
    -------------------------------------------------- */
    function moveFilters() {
      const inner = sidebar.querySelector(".swad-filter-inner");
      if (!inner || sidebar.contains(filterSource)) return;

      const placeholder = document.createElement("div");
      placeholder.className = "swad-filter-placeholder";
      filterSource.parentNode.insertBefore(placeholder, filterSource);

      inner.appendChild(filterSource);
    }

    moveFilters();

    /* --------------------------------------------------
       COLLAPSIBLE MODULES
    -------------------------------------------------- */
    function initModules() {
      const inner = sidebar.querySelector(".swad-filter-inner");
      if (!inner) return;

      const modules = inner.querySelectorAll(".module");

      modules.forEach((mod, index) => {
        if (mod.dataset.swadInit) return;
        mod.dataset.swadInit = "1";

        const header =
          mod.querySelector("h2") ||
          (() => {
            const h = document.createElement("h2");
            h.textContent = "Filters";
            mod.prepend(h);
            return h;
          })();

        const content = document.createElement("div");
        content.className = "swad-module-content";

        [...mod.children].forEach(el => {
          if (el !== header) content.appendChild(el);
        });
        mod.appendChild(content);

        const key = `swad:filter:${location.pathname}:${index}`;
        const stored = localStorage.getItem(key);
        const mobile = window.matchMedia("(max-width:900px)").matches;
        const collapsed = stored ? stored === "closed" : mobile;

        mod.classList.toggle("swad-module-collapsed", collapsed);

        header.setAttribute("role", "button");
        header.setAttribute("tabindex", "0");
        header.setAttribute("aria-expanded", !collapsed);

        let icon = header.querySelector(".swad-toggle-icon");
        if (!icon) {
          icon = document.createElement("span");
          icon.className = "swad-toggle-icon";
          icon.textContent = "▾";
          header.appendChild(icon);
        }

        const toggleModule = () => {
          const isClosed = mod.classList.toggle("swad-module-collapsed");
          header.setAttribute("aria-expanded", !isClosed);
          localStorage.setItem(key, isClosed ? "closed" : "open");
        };

        header.addEventListener("click", e => {
          e.preventDefault();
          toggleModule();
        });

        header.addEventListener("keydown", e => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleModule();
          }
        });
      });
    }

    initModules();
    window.addEventListener("load", initModules, { once: true });

    /* --------------------------------------------------
       RESTORE SIDEBAR STATE
    -------------------------------------------------- */
    if (localStorage.getItem(LS_COLLAPSED) === "true") {
      document.body.classList.add("swad-sidebar-collapsed");
    }

    if (
      localStorage.getItem(LS_OPEN) === "true" &&
      window.matchMedia("(max-width:900px)").matches
    ) {
      sidebar.classList.add("open");
    }

    /* --------------------------------------------------
       TOGGLE HANDLER
    -------------------------------------------------- */
    toggle.addEventListener("click", () => {
      const collapsed = document.body.classList.toggle("swad-sidebar-collapsed");
      localStorage.setItem(LS_COLLAPSED, collapsed);

      if (window.matchMedia("(max-width:900px)").matches) {
        const open = sidebar.classList.toggle("open");
        localStorage.setItem(LS_OPEN, open);
      } else {
        sidebar.classList.remove("open");
        localStorage.setItem(LS_OPEN, "false");
      }

      if (!collapsed) {
        sidebar.querySelector(".swad-filter-inner")?.focus();
      }
    });

    /* --------------------------------------------------
       OUTSIDE CLICK — MOBILE ONLY
    -------------------------------------------------- */
    document.addEventListener("click", e => {
      if (
        window.matchMedia("(max-width:900px)").matches &&
        sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        !toggle.contains(e.target)
      ) {
        sidebar.classList.remove("open");
        localStorage.setItem(LS_OPEN, "false");
      }
    });

    /* --------------------------------------------------
       RESIZE SYNC
    -------------------------------------------------- */
    window.addEventListener("resize", () => {
      if (window.matchMedia("(max-width:900px)").matches) {
        document.body.classList.add("swad-sidebar-collapsed");
      } else {
        const keepCollapsed = localStorage.getItem(LS_COLLAPSED) === "true";
        document.body.classList.toggle("swad-sidebar-collapsed", keepCollapsed);
        sidebar.classList.remove("open");
        localStorage.setItem(LS_OPEN, "false");
      }
    });
  } catch (err) {
    console.error("Swad Admin Sidebar Error:", err);
  }
});
