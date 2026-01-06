import { Link, NavLink } from "react-router-dom";
import { useState, useMemo } from "react";
import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import AccountModal from "./AccountModal";

/* ======================================================
   Navbar — Premium UX Upgrade (Zomato/Blinkit Style)
   • Logo + Navigation Tabs + Cart + Auth + Theme
   • Sticky on scroll
   • Mobile-optimized
====================================================== */

export default function Navbar({ statusOverride } = {}) {
  const { theme, toggleTheme } = useTheme();
  const { user, isAuthenticated, logoutUser } = useAuth();
  const { itemCount, openCheckout } = useCart();
  const [menuOpen, setMenuOpen] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  /* ================= BREAKFAST STATUS ================= */
  const status = useMemo(() => {
    if (statusOverride) return statusOverride;

    const OPEN_START = 8 * 60;      // 08:00 AM
    const OPEN_END = 11.5 * 60;     // 11:30 AM

    const now = new Date();
    const mins = now.getHours() * 60 + now.getMinutes();
    return mins >= OPEN_START && mins <= OPEN_END ? "open" : "closed";
  }, [statusOverride]);

  return (
    <>
      {/* ================= TOP BAR ================= */}
      <header className="sticky top-0 z-40 bg-app/95 backdrop-blur-md border-b border-subtle">
        <div className="h-16 px-4 flex items-center justify-between">

          {/* LEFT: LOGO */}
          <Link
            to="/welcome"
            className="text-lg font-bold tracking-wide text-accent font-heading hover:text-accent/80 transition-colors"
          >
            Swad of Tamil
          </Link>

          {/* CENTER: NAVIGATION TABS (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 bg-surface/50 rounded-full px-2 py-1">
            <NavTab to="/home" icon="🍽️" label="Combos" />
            <NavTab to="/snacks" icon="🍪" label="Snacks" />
            <NavTab to="/subscription" icon="🔁" label="Subscription" />
          </nav>

          {/* RIGHT: ACTIONS */}
          <div className="flex items-center gap-3">
            {/* CART BUTTON */}
            <button
              onClick={openCheckout}
              className="relative h-10 w-10 rounded-full bg-accent text-black flex items-center justify-center hover:bg-accent/90 transition-colors"
              aria-label="View cart"
            >
              🛒
              {itemCount > 0 && (
                <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {itemCount > 99 ? '99+' : itemCount}
                </span>
              )}
            </button>

            {/* AUTH DROPDOWN */}
            <div className="relative">
              {isAuthenticated ? (
                <ProfileDropdown
                  user={user}
                  onLogout={logoutUser}
                />
              ) : (
                <button
                  onClick={() => setShowLogin(true)}
                  className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full bg-surface hover:bg-surface/80 transition-colors"
                >
                  <span className="text-sm font-medium">Login</span>
                </button>
              )}

              {/* MOBILE MENU BUTTON */}
              <button
                onClick={() => setMenuOpen(true)}
                className="md:hidden h-10 w-10 rounded-full border border-subtle flex items-center justify-center hover:bg-surface transition-colors"
                aria-label="Open menu"
              >
                ☰
              </button>
            </div>

            {/* THEME TOGGLE */}
            <button
              onClick={toggleTheme}
              className="h-10 w-10 rounded-full border border-subtle flex items-center justify-center hover:bg-surface transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "🌙" : "☀️"}
            </button>
          </div>
        </div>

        {/* MOBILE NAVIGATION TABS */}
        <div className="md:hidden border-t border-subtle">
          <nav className="flex items-center justify-around px-4 py-2">
            <MobileNavTab to="/home" icon="🍽️" label="Combos" />
            <MobileNavTab to="/snacks" icon="🍪" label="Snacks" />
            <MobileNavTab to="/subscription" icon="🔁" label="Subscription" />
          </nav>
        </div>
      </header>

      {/* ================= MOBILE MENU ================= */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 md:hidden">
          <div className="absolute bottom-0 left-0 right-0 bg-card rounded-t-3xl p-6 max-h-[80vh] overflow-y-auto">

            {/* HEADER */}
            <div className="flex justify-between items-center mb-6">
              <span className="font-semibold font-heading">Swad of Tamil</span>
              <button
                onClick={() => setMenuOpen(false)}
                className="h-9 w-9 rounded-full border border-subtle flex items-center justify-center"
                aria-label="Close menu"
              >
                ✕
              </button>
            </div>

            {/* AUTHENTICATION */}
            {isAuthenticated ? (
              <div className="space-y-4 mb-6">
                <div className="flex items-center gap-3 p-3 bg-surface rounded-lg">
                  <div className="h-10 w-10 rounded-full bg-accent flex items-center justify-center text-black font-bold">
                    👤
                  </div>
                  <div>
                    <div className="font-medium">Hi, {user?.name || user?.phone}</div>
                    <div className="text-sm text-muted">{user?.phone}</div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    logoutUser();
                    setMenuOpen(false);
                  }}
                  className="w-full py-3 text-sm font-medium text-red-400 hover:text-red-300 border border-red-400/20 rounded-lg hover:bg-red-400/10"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="space-y-3 mb-6">
                <button
                  onClick={() => {
                    setShowLogin(true);
                    setMenuOpen(false);
                  }}
                  className="w-full py-3 bg-accent text-black font-semibold rounded-lg hover:bg-accent/90"
                >
                  Login / Sign Up
                </button>
              </div>
            )}

            {/* NAVIGATION LINKS */}
            <div className="space-y-2 mb-6">
              <MobileMenuItem to="/home" onClick={() => setMenuOpen(false)}>
                🏠 Home
              </MobileMenuItem>
              <MobileMenuItem to="/snacks" onClick={() => setMenuOpen(false)}>
                🍪 Snacks
              </MobileMenuItem>
              <MobileMenuItem to="/about" onClick={() => setMenuOpen(false)}>
                ℹ️ About
              </MobileMenuItem>
              <MobileMenuItem to="/my-orders" onClick={() => setMenuOpen(false)}>
                📦 My Orders
              </MobileMenuItem>
            </div>

            {/* STATUS & THEME */}
            <div className="flex items-center justify-between pt-4 border-t border-subtle">
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

      {/* LOGIN MODAL */}
      <AccountModal
        open={showLogin}
        onClose={() => setShowLogin(false)}
        onSuccess={() => setShowLogin(false)}
      />
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

function NavTab({ to, icon, label, disabled }) {
  if (disabled) {
    return (
      <span className="flex items-center gap-2 px-4 py-2 text-muted cursor-not-allowed opacity-50">
        <span>{icon}</span>
        <span className="text-sm font-medium">{label}</span>
      </span>
    );
  }

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
          isActive
            ? "bg-accent text-black"
            : "text-muted hover:text-text hover:bg-surface/50"
        }`
      }
    >
      <span>{icon}</span>
      <span>{label}</span>
    </NavLink>
  );
}

function MobileNavTab({ to, icon, label, disabled }) {
  if (disabled) {
    return (
      <span className="flex flex-col items-center gap-1 p-2 text-muted opacity-50">
        <span className="text-lg">{icon}</span>
        <span className="text-xs">{label}</span>
      </span>
    );
  }

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex flex-col items-center gap-1 p-2 rounded-lg transition-colors ${
          isActive
            ? "bg-accent text-black"
            : "text-muted hover:text-text hover:bg-surface/50"
        }`
      }
    >
      <span className="text-lg">{icon}</span>
      <span className="text-xs font-medium">{label}</span>
    </NavLink>
  );
}

function ProfileDropdown({ user, onLogout }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative hidden md:block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-2 rounded-full bg-surface hover:bg-surface/80 transition-colors"
      >
        <div className="h-6 w-6 rounded-full bg-accent flex items-center justify-center text-black text-sm font-bold">
          👤
        </div>
        <span className="text-sm font-medium">{user?.name || user?.phone}</span>
        <span className="text-xs">▼</span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-48 bg-card border border-subtle rounded-lg shadow-lg py-2 z-20">
            <div className="px-4 py-2 border-b border-subtle">
              <div className="font-medium">{user?.name || user?.phone}</div>
              <div className="text-sm text-muted">{user?.phone}</div>
            </div>
            <button
              onClick={() => {
                onLogout();
                setIsOpen(false);
              }}
              className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-400/10"
            >
              Logout
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function MobileMenuItem({ to, children, onClick }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className="flex items-center gap-3 p-3 rounded-lg hover:bg-surface transition-colors text-text"
    >
      {children}
    </NavLink>
  );
}
