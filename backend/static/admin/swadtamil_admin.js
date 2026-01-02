// Swad admin: move changelist filters into a fixed left sidebar, add collapse toggle
document.addEventListener('DOMContentLoaded', function () {
  try {
    // Find a filter/source module first; if none exists, skip creating sidebar.
    const source = document.getElementById('changelist-filter') || document.querySelector('.change-list .module') || document.querySelector('.sidebar .module');
    if (!source) {
      // No changelist filters on this page (e.g. change_form). Do not render sidebar.
      return;
    }

    // create sidebar container (only when a source is present)
    const sidebar = document.createElement('aside');
    sidebar.id = 'swad-filter-sidebar';
    sidebar.innerHTML = '<div class="swad-filter-inner" tabindex="-1"></div>';
    document.body.appendChild(sidebar);

    // create toggle
    const toggle = document.createElement('button');
    toggle.id = 'swad-filter-toggle';
    toggle.type = 'button';
    toggle.textContent = 'Filters';
    document.body.appendChild(toggle);

    // Ensure admin body has flag for layout
    document.body.classList.add('with-swad-sidebar');

    // Theme toggle: persist light/dark preference and apply class `swad-theme-light`
    const THEME_KEY = 'swad:theme';
    function applyTheme(theme) {
      try {
        if (theme === 'light') document.body.classList.add('swad-theme-light'); else document.body.classList.remove('swad-theme-light');
        const btn = document.getElementById('swad-theme-toggle');
        if (btn) {
          btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
          btn.title = theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme';
        }
        localStorage.setItem(THEME_KEY, theme);
      } catch (err) { /* ignore storage errors */ }
    }

    // Initialize theme from storage or prefers-color-scheme
    try {
      let stored = localStorage.getItem(THEME_KEY);
      if (!stored) stored = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
      applyTheme(stored);
    } catch (err) { /* ignore */ }

    // localStorage keys
    const LS_KEY = 'swad:sidebar-collapsed';
    const LS_OPEN = 'swad:sidebar-open';

    // helper to move (not clone) filter content so event handlers remain intact
    function moveFilters() {
      const inner = sidebar.querySelector('.swad-filter-inner');

      // Preferred id used by Django's templates — look for the actual filter container
      const source = document.getElementById('changelist-filter') || document.querySelector('.change-list .module') || document.querySelector('.sidebar .module');
      if (!source) return;

      // if we've already moved this node (or it's already inside sidebar), do nothing
      if (sidebar.contains(source)) return;

      // create a placeholder so layout doesn't collapse where filters were
      const placeholder = document.createElement('div');
      placeholder.className = 'swad-filter-placeholder';
      source.parentNode.insertBefore(placeholder, source);

      // move the original node (preserves event listeners)
      inner.appendChild(source);

      // mark moved for future checks
      source.dataset.swadMoved = '1';
    }

    // Move the filters from the page into our sidebar
    moveFilters();

    // Init collapsible behavior for each filter module (minimal JS + localStorage)
    function initCollapsibleFilters() {
      const inner = sidebar.querySelector('.swad-filter-inner');
      if (!inner) return;
      const modules = inner.querySelectorAll('.module');
      const pageKeyBase = 'swad:filter:page:' + location.pathname + location.search;

      modules.forEach((mod, idx) => {
        // Avoid double-initialization
        if (mod.dataset.swadCollapsibleInitialized) return;
        mod.dataset.swadCollapsibleInitialized = '1';

        // Find header (Django admin uses h2 inside .module)
        const header = mod.querySelector('h2');

        // Create a content wrapper and move all non-header children into it
        const content = document.createElement('div');
        content.className = 'swad-module-content';
        const children = Array.from(mod.childNodes);
        children.forEach(node => {
          if (header && node === header) return;
          content.appendChild(node);
        });
        mod.appendChild(content);

        // Unique key per page + module index
        const id = pageKeyBase + ':m:' + idx;
        mod.dataset.swadId = id;

        // Make the entire header act as the toggle (keyboard + mouse)
        const stored = localStorage.getItem(id);
        const isMobile = window.matchMedia('(max-width:900px)').matches;
        let collapsed = false;
        if (stored !== null) collapsed = stored === 'closed';
        else collapsed = isMobile;

        // Ensure header exists; create if missing
        let headerEl = header;
        if (!headerEl) {
          headerEl = document.createElement('h2');
          headerEl.textContent = 'Filters';
          mod.insertBefore(headerEl, content);
        }

        // style header for inline layout and append icon
        headerEl.style.display = 'flex';
        headerEl.style.alignItems = 'center';
        headerEl.style.gap = '8px';

        // add an icon element for visual affordance
        let icon = headerEl.querySelector('.swad-toggle-icon');
        if (!icon) {
          icon = document.createElement('span');
          icon.className = 'swad-toggle-icon';
          icon.textContent = '▾';
          headerEl.appendChild(icon);
        }

        // make header keyboard-focusable and announceable
        headerEl.setAttribute('role', 'button');
        headerEl.setAttribute('tabindex', '0');
        headerEl.setAttribute('aria-expanded', collapsed ? 'false' : 'true');

        if (collapsed) mod.classList.add('swad-module-collapsed'); else mod.classList.remove('swad-module-collapsed');

        function toggleHeader(e) {
          // allow keyboard activation on Enter/Space
          if (e.type === 'keydown' && !(e.key === 'Enter' || e.key === ' ')) return;
          if (e.type === 'click') e.preventDefault();
          const nowCollapsed = mod.classList.toggle('swad-module-collapsed');
          headerEl.setAttribute('aria-expanded', nowCollapsed ? 'false' : 'true');
          try { localStorage.setItem(id, nowCollapsed ? 'closed' : 'open'); } catch (err) { /* ignore */ }
        }

        headerEl.addEventListener('click', toggleHeader);
        headerEl.addEventListener('keydown', toggleHeader);
      });
    }

    // Run init after moving filters; safe to call multiple times (idempotent)
    initCollapsibleFilters();

    // Also attempt init again on load (in case filters injected late)
    window.addEventListener('load', function () { initCollapsibleFilters(); }, { once: true });

    // One-time attempt to move filters; avoid MutationObserver for stability/perf
    // Some admin pages load filters synchronously; if filters are injected later
    // this will still run again on window load to attempt the move a second time.
    window.addEventListener('load', moveFilters, { once: true });

    // Restore collapsed/open state from localStorage
    const storedCollapsed = localStorage.getItem(LS_KEY);
    if (storedCollapsed === 'true') {
      document.body.classList.add('swad-sidebar-collapsed');
    }
    const storedOpen = localStorage.getItem(LS_OPEN);
    if (storedOpen === 'true' && window.matchMedia('(max-width:900px)').matches) {
      sidebar.classList.add('open');
    }

    // Toggle behavior
    toggle.addEventListener('click', function () {
      const isCollapsed = document.body.classList.toggle('swad-sidebar-collapsed');
      // persist collapsed state for desktop
      localStorage.setItem(LS_KEY, isCollapsed ? 'true' : 'false');

      // For small screens treat as overlay open/close
      if (window.matchMedia('(max-width:900px)').matches) {
        const isOpen = sidebar.classList.toggle('open');
        localStorage.setItem(LS_OPEN, isOpen ? 'true' : 'false');
      } else {
        // ensure overlay flag reset on desktop
        sidebar.classList.remove('open');
        localStorage.setItem(LS_OPEN, 'false');
      }

      // ensure focus for keyboard users when opening
      if (!isCollapsed) sidebar.querySelector('.swad-filter-inner')?.focus();
    });

    // Wire theme toggle button (if present in header)
    const themeBtn = document.getElementById('swad-theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', function (ev) {
        ev.preventDefault();
        const current = document.body.classList.contains('swad-theme-light') ? 'light' : 'dark';
        const next = current === 'light' ? 'dark' : 'light';
        applyTheme(next);
      });
    }

    // Close overlay on outside click (mobile)
    document.addEventListener('click', function (e) {
      if (window.matchMedia('(max-width:900px)').matches) {
        if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
          const wasOpen = sidebar.classList.contains('open');
          sidebar.classList.remove('open');
          if (wasOpen) localStorage.setItem(LS_OPEN, 'false');
        }
      }
    });

    // keep sidebar width in sync with CSS var in case of responsive changes
    window.addEventListener('resize', () => {
      if (window.matchMedia('(max-width:900px)').matches) {
        document.body.classList.add('swad-sidebar-collapsed');
      } else {
        // respect persisted desktop collapsed state
        const persisted = localStorage.getItem(LS_KEY) === 'true';
        if (persisted) document.body.classList.add('swad-sidebar-collapsed'); else document.body.classList.remove('swad-sidebar-collapsed');
        sidebar.classList.remove('open');
        localStorage.setItem(LS_OPEN, 'false');
      }
    });
  } catch (e) {
    // Fail silently to avoid breaking admin
    console.error('Swad admin sidebar init error', e);
  }
});
// Minimal UI: avoid animations/observers to prioritize stability and performance.
