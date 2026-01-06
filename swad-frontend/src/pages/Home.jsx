import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/* ================= COMPONENTS ================= */
import ComboCard from "../components/ComboCard";
import ItemCardMini from "../components/ItemCardMini";
import SnackCard from "../components/SnackCard";
import SkeletonCard from "../components/SkeletonCard";
import DesktopSidebar from "../components/DesktopSidebar";
import RecommendedSection from "../components/RecommendedSection";
import Carousel from "../components/Carousel";

/* ================= MODALS ================= */
import ProductDetailModal from "../components/ProductDetailModal";
import ItemListModal from "../components/ItemListModal";
import ItemDetailModal from "../components/ItemDetailModal";
import SnackPickerModal from "../components/SnackPickerModal";
import AccountModal from "../components/AccountModal";

/* ================= API ================= */
import {
  fetchCombos,
  fetchPreparedItems,
  fetchSnacks,
  fetchMarketingOffers,
  fetchStoreStatus,
} from "../api";

const TAB_KEY = "swad_home_tab";

/* ======================================================
   DATA HOOK
====================================================== */
function useHomeData() {
  const [state, setState] = useState({
    combos: [],
    items: [],
    snacks: [],
    offers: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const [combos, items, snacks, offers] = await Promise.all([
          fetchCombos(),
          fetchPreparedItems(),
          fetchSnacks(),
          fetchMarketingOffers(),
        ]);

        if (!mounted) return;

        setState({
          combos: Array.isArray(combos) ? combos : [],
          items: Array.isArray(items) ? items : [],
          snacks: Array.isArray(snacks) ? snacks : [],
          offers: Array.isArray(offers) ? offers : [],
          loading: false,
          error: null,
        });
      } catch {
        if (!mounted) return;
        setState((s) => ({
          ...s,
          loading: false,
          error: "Unable to load menu",
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

/* ======================================================
   UI STATE HOOK
====================================================== */
function useHomeUI() {
  const location = useLocation();

  const [tab, setTab] = useState(() => {
    // Check for initialTab from welcome page navigation
    const initialTab = location.state?.initialTab;
    if (initialTab) return initialTab;

    // Otherwise use saved preference or default
    return localStorage.getItem(TAB_KEY) || "combos";
  });

  useEffect(() => {
    localStorage.setItem(TAB_KEY, tab);
  }, [tab]);

  const [activeCombo, setActiveCombo] = useState(null);
  const [activeItem, setActiveItem] = useState(null);
  const [showItems, setShowItems] = useState(false);
  const [showSnacks, setShowSnacks] = useState(false);
  const [showAuth, setShowAuth] = useState(false);

  return {
    tab,
    setTab,

    activeCombo,
    activeItem,

    showItems,
    showSnacks,
    showAuth,

    openCombo: setActiveCombo,
    closeCombo: () => setActiveCombo(null),

    openItem: setActiveItem,
    closeItem: () => setActiveItem(null),

    openItems: () => setShowItems(true),
    closeItems: () => setShowItems(false),

    openSnacks: () => setShowSnacks(true),
    closeSnacks: () => setShowSnacks(false),

    openAuth: () => setShowAuth(true),
    closeAuth: () => setShowAuth(false),
  };
}

/* ======================================================
   DELIVERY URGENCY (FROM API - NO HARDCODED TIMES)
====================================================== */
function useDeliveryUrgency() {
  const [state, setState] = useState({
    text: "",
    color: "text-green-600",
  });

  useEffect(() => {
    const update = async () => {
      try {
        const status = await fetchStoreStatus();
        
        if (!status.is_open) {
          // Store is closed
          setState({
            text: status.message || "Store is currently closed",
            color: "text-red-600",
          });
        } else if (!status.accept_orders) {
          // Store open but not accepting orders
          setState({
            text: "Store open but not accepting orders",
            color: "text-amber-600",
          });
        } else if (status.order_cutoff) {
          // Calculate time until cutoff
          const now = new Date();
          const [hours, minutes] = status.order_cutoff.split(':').map(Number);
          const cutoff = new Date();
          cutoff.setHours(hours, minutes, 0, 0);
          
          // If cutoff is tomorrow, add a day
          if (cutoff <= now) {
            cutoff.setDate(cutoff.getDate() + 1);
          }
          
          const mins = Math.floor((cutoff - now) / 60000);
          
          if (mins <= 0) {
            setState({
              text: "Ordering closed for today",
              color: "text-red-600",
            });
          } else if (mins <= 30) {
            setState({
              text: `Ordering closes in ${mins} min`,
              color: "text-red-600",
            });
          } else if (mins <= 60) {
            setState({
              text: `Ordering closes in ${mins} min`,
              color: "text-amber-600",
            });
          } else {
            const hours = Math.floor(mins / 60);
            setState({
              text: `Ordering closes in ${hours} hour${hours > 1 ? "s" : ""}`,
              color: "text-green-600",
            });
          }
        } else {
          // Store open, accepting orders, no cutoff info
          setState({
            text: "Store is open for orders",
            color: "text-green-600",
          });
        }
      } catch (error) {
        console.warn('Failed to fetch store status:', error);
        setState({
          text: "Unable to check ordering status",
          color: "text-amber-600",
        });
      }
    };

    update();
    const timer = setInterval(update, 60000); // Update every minute
    return () => clearInterval(timer);
  }, []);

  return state;
}

/* ======================================================
   HELPERS
====================================================== */
function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good Morning";
  if (hour < 17) return "Good Afternoon";
  return "Good Evening";
}

/* ======================================================
   HOME
====================================================== */
export default function Home() {
  const { isAuthenticated, checking } = useAuth();

  const { combos, items, snacks, offers, loading, error } = useHomeData();
  const ui = useHomeUI();
  const urgency = useDeliveryUrgency();

  const greeting = getGreeting();

  const currentList = useMemo(() => {
    switch (ui.tab) {
      case "items":
        return items;
      case "snacks":
        return snacks;
      default:
        return combos;
    }
  }, [ui.tab, combos, items, snacks]);

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
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-4">
          <h1 className="text-3xl font-bold font-heading">Fresh Tamil Breakfast</h1>

          <p className="text-lg font-medium text-accent">
            Soft idlis. Hot sambar. Delivered fresh.
          </p>

          <div className="flex flex-wrap gap-4 text-sm text-muted">
            <span className={`flex items-center gap-2 ${urgency.color}`}>
              ⏳ {urgency.text}
            </span>
            <span className="flex items-center gap-2">
              📍 Sector 23C, Chandigarh
            </span>
          </div>

          <div className="flex gap-2 pt-3">
            {[
              ["combos", "Breakfast"],
              ["items", "Items"],
              ["snacks", "Add-ons"],
            ].map(([key, label]) => (
              <button
                key={key}
                onClick={() => ui.setTab(key)}
                className={`px-5 py-2 rounded-full text-sm font-semibold ${
                  ui.tab === key
                    ? "bg-accent text-black"
                    : "bg-card text-muted hover:bg-white/5"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* ================= HERO CTA ROW ================= */}
          <div className="flex flex-col sm:flex-row gap-3 pt-6">
            <button
              onClick={() => ui.setTab("combos")}
              className="flex-1 bg-accent text-black font-semibold py-3 px-6 rounded-lg hover:bg-accent/90 transition-colors text-center"
            >
              🍽️ Order Breakfast
            </button>
            <button
              onClick={() => ui.setTab("subscription")}
              className="flex-1 bg-card border border-subtle text-text font-semibold py-3 px-6 rounded-lg hover:bg-surface transition-colors text-center"
            >
              🔁 Subscribe & Save
            </button>
          </div>
        </div>
      </section>

      {/* ================= TRUST STRIP ================= */}
      <section className="bg-card border-b border-subtle">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 text-sm">
            <div className="flex items-center gap-2 text-green-600">
              <span className="text-lg">✔</span>
              <span className="font-medium">Fresh every morning</span>
            </div>
            <div className="flex items-center gap-2 text-accent">
              <span className="text-lg">👨‍🍳</span>
              <span className="font-medium">Authentic Tamil recipes</span>
            </div>
            <div className="flex items-center gap-2 text-blue-600">
              <span className="text-lg">🚚</span>
              <span className="font-medium">Delivered in 30 mins</span>
            </div>
          </div>
        </div>
      </section>

      {/* ================= RECOMMENDED ================= */}
      <RecommendedSection
        combos={combos}
        snacks={snacks}
        onViewCombo={ui.openCombo}
      />

      {/* ================= GRID ================= */}
      <div className="max-w-7xl mx-auto px-4 py-10 flex gap-8">
        <section className="flex-1">
          <div className="space-y-12">
              {ui.tab === "combos" && (
                <>
                  {/* BEST SELLERS - PREMIUM CAROUSEL */}
                  <section>
                    <h2 className="text-2xl font-bold mb-6 text-foreground">Popular Breakfast</h2>
                    <Carousel
                      itemClassName="w-80"
                      showDots={true}
                      showArrows={true}
                      slidesToShow={{ mobile: 1, tablet: 2, desktop: 3 }}
                      gap="gap-6"
                    >
                      {combos.slice(0, 4).map((c, index) => (
                        <ComboCard
                          key={c.id}
                          combo={c}
                          combos={combos}
                          onView={() => ui.openCombo(c)}
                          onRequireAuth={() =>
                            !isAuthenticated && ui.openAuth()
                          }
                          featured={index === 0}
                          size={index === 0 ? "large" : "normal"}
                        />
                      ))}
                    </Carousel>
                  </section>

                  {/* FOR FAMILIES - PREMIUM CAROUSEL */}
                  <section>
                    <h2 className="text-2xl font-bold mb-6 text-foreground">Family Meals</h2>
                    <Carousel
                      itemClassName="w-80"
                      showDots={true}
                      showArrows={true}
                      slidesToShow={{ mobile: 1, tablet: 2, desktop: 3 }}
                      gap="gap-6"
                    >
                      {combos.slice(4, 8).map((c) => (
                        <ComboCard
                          key={c.id}
                          combo={c}
                          combos={combos}
                          onView={() => ui.openCombo(c)}
                          onRequireAuth={() =>
                            !isAuthenticated && ui.openAuth()
                          }
                        />
                      ))}
                    </Carousel>
                  </section>

                  {/* QUICK MEALS - PREMIUM CAROUSEL */}
                  {combos.slice(8).length > 0 && (
                    <section>
                      <h2 className="text-2xl font-bold mb-6 text-foreground">Quick Meals</h2>
                      <Carousel
                        itemClassName="w-64"
                        showDots={true}
                        showArrows={true}
                        slidesToShow={{ mobile: 2, tablet: 4, desktop: 5 }}
                        gap="gap-4"
                      >
                        {combos.slice(8).map((c) => (
                          <ComboCard
                            key={c.id}
                            combo={c}
                            combos={combos}
                            onView={() => ui.openCombo(c)}
                            onRequireAuth={() =>
                              !isAuthenticated && ui.openAuth()
                            }
                          />
                        ))}
                      </Carousel>
                    </section>
                  )}
                </>
              )}

              {ui.tab === "items" && (
                <section>
                  <h2 className="text-2xl font-bold mb-6 text-foreground">Prepared Items</h2>
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
              )}

              {ui.tab === "snacks" && (
                <section>
                  <h2 className="text-2xl font-bold mb-6 text-foreground">Add-ons</h2>
                  <Carousel
                    itemClassName="w-64"
                    showDots={true}
                    showArrows={true}
                    slidesToShow={{ mobile: 2, tablet: 3, desktop: 4 }}
                    gap="gap-4"
                  >
                    {snacks.map((s) => (
                      <SnackCard key={s.id} snack={s} />
                    ))}
                  </Carousel>
                </section>
              )}

              {/* Show skeleton cards only during loading */}
              {loading && !currentList.length && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <SkeletonCard key={i} />
                  ))}
                </div>
              )}

              {/* Show empty state when loaded but no items */}
              {!loading && !error && !currentList.length && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="text-6xl mb-4">
                    {ui.tab === "combos" && "🍽️"}
                    {ui.tab === "items" && "🥘"}
                    {ui.tab === "snacks" && "🍪"}
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    {ui.tab === "combos" && "No Breakfast Available"}
                    {ui.tab === "items" && "No Items Available"}
                    {ui.tab === "snacks" && "No Add-ons Available"}
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
                    Unable to Load Menu
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
          </section>

        <DesktopSidebar marketingOffers={offers} />
      </div>

      {/* ================= MODALS ================= */}
      {ui.activeCombo && (
        <ProductDetailModal
          product={ui.activeCombo}
          onClose={ui.closeCombo}
          onOpenItems={ui.openItems}
          onOpenSnacks={ui.openSnacks}
        />
      )}

      <ItemListModal
        open={ui.showItems}
        items={items}
        onClose={ui.closeItems}
        onSelectItem={(item) => {
          ui.openItem(item);
          ui.closeItems();
        }}
      />

      <ItemDetailModal
        open={!!ui.activeItem}
        item={ui.activeItem}
        onClose={ui.closeItem}
      />

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
