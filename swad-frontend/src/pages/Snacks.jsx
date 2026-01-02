import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

/* ================= COMPONENTS ================= */
import SnackCard from "../components/SnackCard";
import SkeletonCard from "../components/SkeletonCard";
import SnackPickerModal from "../components/SnackPickerModal";
import ItemDetailModal from "../components/ItemDetailModal";

/* ================= API ================= */
import { fetchSnacks } from "../api";

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
  /* ================= DATA ================= */
  const [snacks, setSnacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /* ================= UI ================= */
  const [category, setCategory] = useState("all");
  const [activeSnack, setActiveSnack] = useState(null);
  const [showSnackPicker, setShowSnackPicker] = useState(false);

  /* ================= LOAD ================= */
  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchSnacks();
        if (!mounted) return;

        setSnacks(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("fetchSnacks failed", err);
        mounted && setError("Unable to load snacks.");
      } finally {
        mounted && setLoading(false);
      }
    }

    load();
    return () => (mounted = false);
  }, []);

  /* ================= CATEGORIES ================= */
  const categories = useMemo(() => {
    const set = new Set();
    snacks.forEach((s) => s.category && set.add(s.category));
    return ["all", ...Array.from(set)];
  }, [snacks]);

  const visible = useMemo(() => {
    if (category === "all") return snacks;
    return snacks.filter((s) => s.category === category);
  }, [snacks, category]);

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
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">

        {/* ================= CATEGORY PILLS ================= */}
        {categories.length > 1 && (
          <div className="mb-6 flex gap-3 overflow-x-auto">
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  category === c
                    ? "bg-accent text-black"
                    : "bg-white/5 text-muted"
                }`}
              >
                {c === "all" ? "All" : c}
              </button>
            ))}
          </div>
        )}

        {/* ================= GRID ================= */}
        {visible.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
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
            onClick={() => setShowSnackPicker(true)}
            className="flex-1 py-2 rounded-xl bg-accent text-black text-sm font-semibold"
          >
            Quick Snack Order
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
