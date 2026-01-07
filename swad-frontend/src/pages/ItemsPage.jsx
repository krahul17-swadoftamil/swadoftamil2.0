import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

/* ================= COMPONENTS ================= */
import ItemCardMini from "../components/ItemCardMini";
import SkeletonCard from "../components/SkeletonCard";

/* ================= MODALS ================= */
import ItemDetailModal from "../components/ItemDetailModal";
import AccountModal from "../components/AccountModal";

/* ================= API ================= */
import { fetchPreparedItems } from "../api";

function useItemsData() {
  const [state, setState] = useState({
    items: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const items = await fetchPreparedItems();

        if (!mounted) return;

        setState({
          items: Array.isArray(items) ? items : [],
          loading: false,
          error: null,
        });
      } catch {
        if (!mounted) return;
        setState((s) => ({
          ...s,
          loading: false,
          error: "Unable to load items",
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

function useItemsUI() {
  const [activeItem, setActiveItem] = useState(null);
  const [showAuth, setShowAuth] = useState(false);

  return {
    activeItem,
    showAuth,

    openItem: setActiveItem,
    closeItem: () => setActiveItem(null),

    openAuth: () => setShowAuth(true),
    closeAuth: () => setShowAuth(false),
  };
}

export default function ItemsPage() {
  const { isAuthenticated, checking } = useAuth();

  const { items, loading, error } = useItemsData();
  const ui = useItemsUI();

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
        <div className="max-w-7xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold font-heading">Our Kitchen</h1>
          <p className="text-lg font-medium text-accent mt-2">
            Fresh ingredients, traditional recipes, made with love
          </p>
          <div className="flex flex-wrap gap-6 mt-6 text-sm text-muted">
            <div className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>Sourced daily from local markets</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>Authentic Tamil Nadu recipes</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>Prepared fresh every morning</span>
            </div>
          </div>
        </div>
      </section>

      {/* ================= GRID ================= */}
      <div className="max-w-7xl mx-auto px-4 py-10">
        <section>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {items.map((i) => (
              <ItemCardMini
                key={i.id}
                item={i}
                onView={() => ui.openItem(i)}
              />
            ))}
          </div>
        </section>

        {/* Show skeleton cards only during loading */}
        {loading && !items.length && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Show empty state when loaded but no items */}
        {!loading && !error && !items.length && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="text-6xl mb-4">🥘</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No Items Available
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
              Unable to Load Items
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
      <ItemDetailModal
        open={!!ui.activeItem}
        item={ui.activeItem}
        onClose={ui.closeItem}
      />

      {!checking && ui.showAuth && !isAuthenticated && (
        <AccountModal open onClose={ui.closeAuth} />
      )}
    </main>
  );
}