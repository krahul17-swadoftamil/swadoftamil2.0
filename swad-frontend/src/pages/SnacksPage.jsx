import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

/* ================= COMPONENTS ================= */
import SnackCard from "../components/SnackCard";
import Carousel from "../components/Carousel";

/* ================= MODALS ================= */
import SnackPickerModal from "../components/SnackPickerModal";
import AccountModal from "../components/AccountModal";

/* ================= API ================= */
import { fetchSnacks } from "../api";

function useSnacksData() {
  const [state, setState] = useState({
    snacks: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const snacks = await fetchSnacks();

        if (!mounted) return;

        setState({
          snacks: Array.isArray(snacks) ? snacks : [],
          loading: false,
          error: null,
        });
      } catch {
        if (!mounted) return;
        setState((s) => ({
          ...s,
          loading: false,
          error: "Unable to load add-ons",
        }));
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  return state;
}

function useSnacksUI() {
  const [showSnacks, setShowSnacks] = useState(false);
  const [showAuth, setShowAuth] = useState(false);

  return {
    showSnacks,
    showAuth,

    openSnacks: () => setShowSnacks(true),
    closeSnacks: () => setShowSnacks(false),

    openAuth: () => setShowAuth(true),
    closeAuth: () => setShowAuth(false),
  };
}

export default function SnacksPage() {
  const { isAuthenticated, checking } = useAuth();

  const { snacks, loading, error } = useSnacksData();
  const ui = useSnacksUI();

  if (checking || loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-muted">
        Loading…
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-accent">
        {error}
      </div>
    );
  }

  return (
    <main className="bg-app text-text">
      {/* ================= HERO ================= */}
      <section className="bg-surface border-b border-subtle">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-lg font-medium text-muted-foreground">Add-ons</h1>
          <p className="text-sm text-muted mt-1">
            Optional extras to complement your meal
          </p>
        </div>
      </section>

      {/* ================= GRID ================= */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <section>
          <Carousel
            itemClassName="w-48"
            showDots={true}
            showArrows={true}
            slidesToShow={{ mobile: 2, tablet: 4, desktop: 6 }}
            gap="gap-3"
          >
            {snacks.map((s) => (
              <SnackCard key={s.id} snack={s} />
            ))}
          </Carousel>
        </section>

        {/* Show empty state when loaded but no snacks */}
        {!loading && !error && !snacks.length && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="text-6xl mb-4">🍪</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No Add-ons Available
            </h3>
            <p className="text-muted max-w-md">
              Check back soon!
            </p>
          </div>
        )}

        {/* Show error state */}
        {error && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="text-6xl mb-4">⚠️</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              Unable to Load Add-ons
            </h3>
            <p className="text-muted max-w-md mb-4">
              Please refresh the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2 bg-accent text-black rounded-full font-semibold hover:bg-accent/90 transition-colors"
            >
              Refresh Page
            </button>
          </div>
        )}
      </div>

      {/* ================= MODALS ================= */}
      <SnackPickerModal
        open={ui.showSnacks}
        snacks={snacks}
        onClose={ui.closeSnacks}
      />

      {!checking && ui.showAuth && !isAuthenticated && (
        <AccountModal open onClose={ui.closeAuth} />
      )}
    </main>
  );
}