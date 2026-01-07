import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

/* ================= COMPONENTS ================= */
import ComboCard from "../components/ComboCard";
import SkeletonCard from "../components/SkeletonCard";
import DesktopSidebar from "../components/DesktopSidebar";
import RecommendedSection from "../components/RecommendedSection";
import Carousel from "../components/Carousel";
import BreakfastWindow from "../components/BreakfastWindow";
import SmartReOrder from "../components/SmartReOrder";
import LoyaltyIndicator from "../components/LoyaltyIndicator";
import ContextualSignIn from "../components/ContextualSignIn";

/* ================= MODALS ================= */
import ProductDetailModal from "../components/ProductDetailModal";
import AccountModal from "../components/AccountModal";

/* ================= API ================= */
import {
  fetchCombos,
  fetchSnacks,
  fetchMarketingOffers,
} from "../api";

/* ======================================================
   DATA HOOK
====================================================== */
function useHomeData() {
  const [state, setState] = useState({
    combos: [],
    snacks: [],
    offers: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const [combos, snacks, offers] = await Promise.all([
          fetchCombos(),
          fetchSnacks(),
          fetchMarketingOffers(),
        ]);

        if (!mounted) return;

        setState({
          combos: Array.isArray(combos) ? combos : [],
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
  const [activeCombo, setActiveCombo] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [showContextualSignIn, setShowContextualSignIn] = useState(false);

  return {
    activeCombo,

    showAuth,
    showContextualSignIn,

    openCombo: setActiveCombo,
    closeCombo: () => setActiveCombo(null),

    openAuth: () => setShowAuth(true),
    closeAuth: () => setShowAuth(false),

    openContextualSignIn: () => setShowContextualSignIn(true),
    closeContextualSignIn: () => setShowContextualSignIn(false),
  };
}

/* ======================================================
   HOME
====================================================== */
export default function Home() {
  const { isAuthenticated, checking } = useAuth();

  const { combos, snacks, offers, loading, error } = useHomeData();
  const ui = useHomeUI();

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
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold font-heading">Fresh Tamil Breakfast</h1>
            <p className="text-lg text-muted">Soft idlis. Hot sambar. Delivered fresh.</p>
            
            {/* EMOTIONAL PULL - AUTHENTICITY MESSAGE */}
            <div className="pt-2">
              <p className="text-sm font-medium text-accent/80 italic">
                Same taste. Every morning. No shortcuts.
              </p>
            </div>

            {/* WHY SWAD OF TAMIL - DIFFERENTIATION */}
            <div className="pt-4 space-y-1">
              <h3 className="text-sm font-semibold text-foreground mb-2">Why Swad of Tamil?</h3>
              <ul className="text-sm text-muted space-y-1">
                <li>• Fixed menu, fixed taste</li>
                <li>• Cooked fresh every morning</li>
                <li>• Ingredients shown openly</li>
              </ul>
            </div>
          </div>

          {/* BREAKFAST WINDOW - LIVE TIMER */}
          <div className="flex justify-center">
            <BreakfastWindow />
          </div>

          {/* SMART RE-ORDER - 1-TAP FEATURE */}
          <SmartReOrder />

          {/* SOFT LOYALTY INDICATOR - EMOTIONAL CONNECTION */}
          <LoyaltyIndicator />

        </div>
      </section>

      {/* ================= TRUST STRIP ================= */}
      <section className="bg-card border-b border-subtle">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-8 text-sm text-muted">
            <span>Fresh every morning</span>
            <span>Authentic Tamil recipes</span>
            <span>Delivered in 30 mins</span>
          </div>
        </div>
      </section>

      {/* ================= RECOMMENDED ================= */}
      <RecommendedSection
        combos={combos}
        snacks={snacks}
        onViewCombo={ui.openCombo}
        onViewSnack={ui.openCombo}
        onRequireAuth={ui.openContextualSignIn}
        isAuthenticated={isAuthenticated}
      />

      {/* ================= GRID ================= */}
      <div className="max-w-7xl mx-auto px-4 py-10 flex gap-8">
        <section className="flex-1">
          <div className="space-y-12">
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
                        onRequireAuth={ui.openContextualSignIn}
                        isAuthenticated={isAuthenticated}
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
                        onRequireAuth={ui.openContextualSignIn}
                        isAuthenticated={isAuthenticated}
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
                          onRequireAuth={ui.openContextualSignIn}
                          isAuthenticated={isAuthenticated}
                        />
                      ))}
                    </Carousel>
                  </section>
                )}
              </>

              {/* Show skeleton cards only during loading */}
              {loading && !combos.length && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <SkeletonCard key={i} />
                  ))}
                </div>
              )}

              {/* Show empty state when loaded but no items */}
              {!loading && !error && !combos.length && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="text-6xl mb-4">
                    🍽️
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    No Breakfast Available
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
          isAuthenticated={isAuthenticated}
          onRequireAuth={ui.openContextualSignIn}
        />
      )}

      {!checking && ui.showAuth && !isAuthenticated && (
        <AccountModal open onClose={ui.closeAuth} />
      )}

      {ui.showContextualSignIn && (
        <ContextualSignIn
          onContinue={() => {
            ui.closeContextualSignIn();
            ui.openAuth();
          }}
          onClose={ui.closeContextualSignIn}
        />
      )}
    </main>
  );
}
