import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

/* ================= COMPONENTS ================= */
import SnackCard from "../components/SnackCard";
import SkeletonCard from "../components/SkeletonCard";
import SnackPickerModal from "../components/SnackPickerModal";
import ItemDetailModal from "../components/ItemDetailModal";

/* ================= API ================= */
import { fetchSnacks, fetchSnackRegions } from "../api";

/* ================= CONTEXT ================= */
import { useCart } from "../context/CartContext";

/* ======================================================
   Snacks — Premium Snack Experience
   Browse • Add • Upsell to Breakfast
====================================================== */

function EmptyState() {
  return (
    <div className="py-24 text-center">
      <p className="text-base text-muted">
        Our handmade snacks are taking a short rest.
      </p>
      <p className="mt-1 text-sm text-muted">
        Crafted in small batches — check back soon.
      </p>
    </div>
  );
}

export default function Snacks() {
  const { snackCount, openCheckout } = useCart();
  /* ================= DATA ================= */
  const [snacks, setSnacks] = useState([]);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /* ================= FILTERS ================= */
  const [category, setCategory] = useState("all");
  const [region, setRegion] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [priceRange, setPriceRange] = useState("all");

  /* ================= UI ================= */
  const [activeSnack, setActiveSnack] = useState(null);
  const [showSnackPicker, setShowSnackPicker] = useState(false);

  /* ================= LOAD ================= */
  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const [snacksData, regionsData] = await Promise.all([
          fetchSnacks(),
          fetchSnackRegions()
        ]);

        if (!mounted) return;

        setSnacks(Array.isArray(snacksData) ? snacksData : []);
        setRegions(Array.isArray(regionsData) ? regionsData : []);
      } catch (err) {
        console.error("Failed to load snacks data", err);
        mounted && setError("Unable to load snacks.");
      } finally {
        mounted && setLoading(false);
      }
    }

    load();
    return () => (mounted = false);
  }, []);

  /* ================= FILTERING & SORTING ================= */
  const visible = useMemo(() => {
    let filtered = snacks;

    // Category filter
    if (category !== "all") {
      filtered = filtered.filter((s) => s.category === category);
    }

    // Region filter
    if (region !== "all") {
      filtered = filtered.filter((s) => s.region === region);
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((s) =>
        s.name.toLowerCase().includes(query) ||
        s.description.toLowerCase().includes(query)
      );
    }

    // Price range filter
    if (priceRange !== "all") {
      filtered = filtered.filter((s) => {
        const price = s.selling_price;
        switch (priceRange) {
          case "under-50": return price < 50;
          case "50-100": return price >= 50 && price <= 100;
          case "100-200": return price >= 100 && price <= 200;
          case "over-200": return price > 200;
          default: return true;
        }
      });
    }

    // Sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "price-low":
          return a.selling_price - b.selling_price;
        case "price-high":
          return b.selling_price - a.selling_price;
        case "name":
        default:
          return a.name.localeCompare(b.name);
      }
    });

    return filtered;
  }, [snacks, category, region, searchQuery, sortBy, priceRange]);

  /* ================= LOADING ================= */
  if (loading) {
    return (
      <div className="min-h-screen bg-app text-white pb-24">
        <main className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-5">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-app flex items-center justify-center text-accent">
        {error}
      </div>
    );
  }

  /* ================= RENDER ================= */
  return (
    <div className="min-h-screen bg-app text-white pb-28">

      {/* ================= HERO ================= */}
      <header className="sticky top-0 z-30 bg-app/90 backdrop-blur border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-lg font-semibold text-accent">
            Handmade Snacks
          </h1>
          <p className="mt-1 text-sm text-muted max-w-xl">
            Small-batch snacks that pair perfectly with breakfast.
          </p>

          {/* ================= SEARCH ================= */}
          <div className="mt-4">
            <input
              type="text"
              placeholder="Search snacks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-muted focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>

          {/* ================= FILTERS ================= */}
          <div className="mt-4 space-y-3">
            {/* Sort & Price Range */}
            <div className="flex gap-3">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/50"
              >
                <option value="name">Sort by Name</option>
                <option value="price-low">Price: Low to High</option>
                <option value="price-high">Price: High to Low</option>
              </select>

              <select
                value={priceRange}
                onChange={(e) => setPriceRange(e.target.value)}
                className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/50"
              >
                <option value="all">All Prices</option>
                <option value="under-50">Under ₹50</option>
                <option value="50-100">₹50 - ₹100</option>
                <option value="100-200">₹100 - ₹200</option>
                <option value="over-200">Over ₹200</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">

        {/* ================= FEATURED SNACKS ================= */}
        {snacks.filter(s => s.is_featured).length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-accent mb-4">Featured Snacks</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {snacks
                .filter(s => s.is_featured)
                .slice(0, 6)
                .map((snack) => (
                  <SnackCard
                    key={`featured-${snack.id}`}
                    snack={snack}
                    onView={() => setActiveSnack(snack)}
                  />
                ))}
            </div>
          </section>
        )}

        {/* ================= FILTERS ================= */}
        <div className="space-y-4">
          {/* Region Pills */}
          {regions.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-muted mb-2">Regions</h3>
              <div className="flex gap-2 overflow-x-auto pb-1">
                <button
                  onClick={() => setRegion("all")}
                  className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                    region === "all"
                      ? "bg-accent text-black"
                      : "bg-white/5 text-muted hover:bg-white/10"
                  }`}
                >
                  All Regions
                </button>
                {regions.map((r) => (
                  <button
                    key={r.value}
                    onClick={() => setRegion(r.value)}
                    className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                      region === r.value
                        ? "bg-accent text-black"
                        : "bg-white/5 text-muted hover:bg-white/10"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Category Pills */}
          <div>
            <h3 className="text-sm font-medium text-muted mb-2">Categories</h3>
            <div className="flex gap-2 overflow-x-auto pb-1">
              <button
                onClick={() => setCategory("all")}
                className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                  category === "all"
                    ? "bg-accent text-black"
                    : "bg-white/5 text-muted hover:bg-white/10"
                }`}
              >
                All Categories
              </button>
              {["mixture", "chips", "sweet", "savory"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                    category === cat
                      ? "bg-accent text-black"
                      : "bg-white/5 text-muted hover:bg-white/10"
                  }`}
                >
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ================= RESULTS INFO ================= */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted">
            {visible.length} snack{visible.length !== 1 ? 's' : ''} found
          </p>
          {(searchQuery || category !== "all" || region !== "all" || priceRange !== "all") && (
            <button
              onClick={() => {
                setCategory("all");
                setRegion("all");
                setSearchQuery("");
                setPriceRange("all");
                setSortBy("name");
              }}
              className="text-sm text-accent hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* ================= GRID ================= */}
        {visible.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {visible.map((snack) => (
              <SnackCard
                key={snack.id}
                snack={snack}
                onView={() => setActiveSnack(snack)}
              />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </main>

      {/* ================= STICKY CTA ================= */}
      <div className="fixed bottom-0 inset-x-0 z-40 bg-app/95 backdrop-blur border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex gap-3">
          <Link
            to="/"
            className="flex-1 text-center py-2 rounded-xl bg-white/10 text-sm"
          >
            Order Breakfast
          </Link>
          <button
            onClick={() => snackCount > 0 ? openCheckout() : setShowSnackPicker(true)}
            className="flex-1 py-2 rounded-xl bg-accent text-black text-sm font-semibold"
          >
            {snackCount > 0 ? `Checkout ${snackCount} Snack${snackCount > 1 ? 's' : ''}` : 'Quick Snack Order'}
          </button>
        </div>
      </div>

      {/* ================= MINI SNACK MODAL ================= */}
      <ItemDetailModal
        open={!!activeSnack}
        item={activeSnack}
        onClose={() => setActiveSnack(null)}
      />

      {/* ================= SNACK PICKER ================= */}
      <SnackPickerModal
        open={showSnackPicker}
        snacks={snacks}
        onClose={() => setShowSnackPicker(false)}
      />
    </div>
  );
}
