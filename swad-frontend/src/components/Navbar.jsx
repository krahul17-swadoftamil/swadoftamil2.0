import { Link, NavLink } from "react-router-dom";
import { useState, useEffect } from "react";
import { useTheme } from "../context/ThemeContext";

/* ======================================================
   Navbar — Clean & Checkout-Safe
   • Brand + Status only
   • No cart / checkout logic
   • Mobile-first
====================================================== */

export default function Navbar({ statusOverride } = {}) {
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const [status, setStatus] = useState("open");

  /* ================= BREAKFAST STATUS ================= */
  useEffect(() => {
    if (statusOverride) {
      setStatus(statusOverride);
      return;
    }

    const OPEN_START = 8 * 60;      // 08:00 AM
    const OPEN_END = 11.5 * 60;     // 11:30 AM

    function evaluateStatus() {
      const now = new Date();
      const mins = now.getHours() * 60 + now.getMinutes();
      return mins >= OPEN_START && mins <= OPEN_END
        ? "open"
        : "closed";
    }

    setStatus(evaluateStatus());
    const timer = setInterval(() => {
      setStatus(evaluateStatus());
    }, 60 * 1000);

    return () => clearInterval(timer);
  }, [statusOverride]);

  return (
    <>
      {/* ================= TOP BAR ================= */}
      <header className="sticky top-0 z-40 bg-app border-b border-subtle backdrop-blur">
        <div className="h-14 px-4 flex items-center justify-between">

          {/* BRAND */}
          <Link
            to="/"
            className="text-sm font-bold tracking-wide text-accent"
          >
            Swad of Tamil
          </Link>

          {/* DESKTOP NAV */}
          <nav className="hidden md:flex items-center gap-6">
            <NavItem to="/">Home</NavItem>
            <NavItem to="/snacks">Snacks</NavItem>
            <NavItem to="/about">About</NavItem>
            <NavItem to="/my-orders">My Orders</NavItem>

            <button
              onClick={toggleTheme}
              className="h-8 w-8 rounded-full border border-subtle flex items-center justify-center"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "🌙" : "☀️"}
            </button>
          </nav>

          {/* MOBILE CONTROLS */}
          <div className="flex items-center gap-3 md:hidden">
            <StatusPill status={status} />

            <button
              onClick={() => setMenuOpen(true)}
              className="h-9 w-9 rounded-full border border-subtle flex items-center justify-center"
              aria-label="Open menu"
            >
              ☰
            </button>
          </div>
        </div>
      </header>

      {/* ================= MOBILE MENU ================= */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 bg-black/60">
          <div className="absolute bottom-0 left-0 right-0 bg-card rounded-t-3xl p-6">

            {/* HEADER */}
            <div className="flex justify-between items-center mb-6">
              <span className="font-semibold">Swad of Tamil</span>

              <button
                onClick={() => setMenuOpen(false)}
                className="h-9 w-9 rounded-full border border-subtle flex items-center justify-center"
                aria-label="Close menu"
              >
                ✕
              </button>
            </div>

            {/* LINKS */}
            <div className="flex flex-col gap-5">
              <MobileNavItem to="/" onClick={() => setMenuOpen(false)}>
                Home
              </MobileNavItem>

              <MobileNavItem to="/snacks" onClick={() => setMenuOpen(false)}>
                Snacks
              </MobileNavItem>

              <MobileNavItem to="/about" onClick={() => setMenuOpen(false)}>
                About
              </MobileNavItem>

              <MobileNavItem to="/my-orders" onClick={() => setMenuOpen(false)}>
                My Orders
              </MobileNavItem>
            </div>

            {/* FOOTER */}
            <div className="mt-8 flex items-center justify-between">
              <StatusPill status={status} />

              <button
                onClick={toggleTheme}
                className="h-9 w-9 rounded-full border border-subtle flex items-center justify-center"
                aria-label="Toggle theme"
              >
                {theme === "dark" ? "🌙" : "☀️"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/* ======================================================
   UI SUB COMPONENTS
====================================================== */

function StatusPill({ status }) {
  const styles = {
    open: "bg-green-500/15 text-green-400",
    closed: "bg-red-500/15 text-red-400",
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-medium ${styles[status]}`}
    >
      {status === "open" ? "Breakfast Live" : "Closed"}
    </span>
  );
}

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        isActive
          ? "text-accent font-semibold border-b-2 border-accent pb-1"
          : "text-muted hover:text-text"
      }
    >
      {children}
    </NavLink>
  );
}

function MobileNavItem({ to, children, onClick }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className="text-lg font-medium text-text"
    >
      {children}
    </NavLink>
  );
}
