import { useEffect, useState } from "react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useTransform,
} from "framer-motion";

/* ================= COMPONENTS ================= */
import ComboCard from "../components/ComboCard";
import ItemCardMini from "../components/ItemCardMini";
import SnackCard from "../components/SnackCard";
import SkeletonCard from "../components/SkeletonCard";

/* ================= MODALS ================= */
import ProductDetailModal from "../components/ProductDetailModal";
import ItemListModal from "../components/ItemListModal";
import ItemDetailModal from "../components/ItemDetailModal";
import SnackPickerModal from "../components/SnackPickerModal";

/* ================= API ================= */
import {
  fetchCombos,
  fetchPreparedItems,
  fetchSnacks,
} from "../api";

/* ================= STORAGE KEYS ================= */
const TAB_KEY = "swad_home_tab";
const TAB_DATE_KEY = "swad_home_tab_date";
const SCROLL_KEY = "swad_home_scroll";
const LAST_PRODUCT_KEY = "swad_last_product";

/* ================= TIME WINDOW ================= */
const BREAKFAST_START = 9.5;  // 09:30
const BREAKFAST_END = 15.5;   // 15:30

const isBreakfastTime = () => {
  const now = new Date();
  const h = now.getHours() + now.getMinutes() / 60;
  return h >= BREAKFAST_START && h <= BREAKFAST_END;
};

/* ======================================================
   HOME — Swad of Tamil (QSR UX Edition)
====================================================== */

export default function Home() {
  /* ================= DATA ================= */
  const [combos, setCombos] = useState(null);
  const [items, setItems] = useState(null);
  const [snacks, setSnacks] = useState(null);

  /* ================= UI STATE ================= */
  const [activeCombo, setActiveCombo] = useState(null);
  const [activeItem, setActiveItem] = useState(null);
  const [showItemList, setShowItemList] = useState(false);
  const [showSnacks, setShowSnacks] = useState(false);
  const [error, setError] = useState(null);

  /* ================= INITIAL TAB ================= */
  const resolveInitialTab = () => {
    const params = new URLSearchParams(window.location.search);
    const urlTab = params.get("tab");
    if (urlTab) return urlTab;

    const today = new Date().toDateString();
    const savedDate = localStorage.getItem(TAB_DATE_KEY);

    if (savedDate !== today) {
      localStorage.clear();
      localStorage.setItem(TAB_DATE_KEY, today);
      return isBreakfastTime() ? "combos" : "snacks";
    }

    return (
      localStorage.getItem(TAB_KEY) ||
      (isBreakfastTime() ? "combos" : "snacks")
    );
  };

  const [tab, setTab] = useState(resolveInitialTab);

  /* ================= HEADER SCROLL ================= */
  const { scrollY } = useScroll();
  const headerScale = useTransform(scrollY, [0, 120], [1, 0.9]);
  const headerOpacity = useTransform(scrollY, [0, 120], [1, 0.85]);

  /* ================= LOAD ALL DATA ================= */
  useEffect(() => {
    let alive = true;

    Promise.all([
      fetchCombos(),
      fetchPreparedItems(),
      fetchSnacks(),
    ])
      .then(([c, i, s]) => {
        if (!alive) return;
        setCombos(Array.isArray(c) ? c : []);
        setItems(Array.isArray(i) ? i : []);
        setSnacks(Array.isArray(s) ? s : []);
      })
      .catch(() => setError("Unable to load menu"));

    return () => (alive = false);
  }, []);

  /* ================= TAB SYNC ================= */
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", tab);
    window.history.replaceState({}, "", `?${params}`);
    localStorage.setItem(TAB_KEY, tab);
  }, [tab]);

  /* ================= SCROLL MEMORY ================= */
  useEffect(() => {
    const onScroll = () => {
      const map = JSON.parse(localStorage.getItem(SCROLL_KEY) || "{}");
      map[tab] = window.scrollY;
      localStorage.setItem(SCROLL_KEY, JSON.stringify(map));
    };
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, [tab]);

  useEffect(() => {
    const map = JSON.parse(localStorage.getItem(SCROLL_KEY) || "{}");
    window.scrollTo({ top: map[tab] || 0 });
  }, [tab]);

  /* ================= RESTORE LAST PRODUCT ================= */
  useEffect(() => {
    const last = JSON.parse(localStorage.getItem(LAST_PRODUCT_KEY) || "null");
    if (!last) return;

    if (last.type === "combo") setActiveCombo(last.data);
    if (last.type === "item") setActiveItem(last.data);
  }, []);

  const rememberProduct = (type, data) => {
    localStorage.setItem(
      LAST_PRODUCT_KEY,
      JSON.stringify({ type, data })
    );
  };

  /* ================= CURRENT TAB DATA ================= */
  const currentData =
    tab === "combos" ? combos :
    tab === "items" ? items :
    snacks;

  const isLoading = currentData === null;

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-accent">
        {error}
      </div>
    );
  }

  /* ================= RENDER ================= */
  return (
    <main className="bg-app text-text">
      {/* ================= HEADER ================= */}
      <motion.header
        style={{ scale: headerScale, opacity: headerOpacity }}
        className="sticky top-0 z-30 bg-app/80 backdrop-blur"
      >
        <div className="max-w-7xl mx-auto px-4 pt-10 pb-6">
          <h1 className="text-3xl sm:text-4xl font-extrabold">
            Authentic Tamil Breakfast
          </h1>

          <nav className="mt-6 flex gap-2">
            {[
              ["combos", "Breakfast Combos"],
              ["items", "Individual Items"],
              ["snacks", "Snacks & Add-ons"],
            ].map(([key, label]) => (
              <motion.button
                key={key}
                layout
                onClick={() => setTab(key)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition
                  ${
                    tab === key
                      ? "bg-accent text-black"
                      : "bg-surface text-muted hover:bg-white/5"
                  }`}
              >
                {label}
              </motion.button>
            ))}
          </nav>
        </div>
      </motion.header>

      {/* ================= GRID ================= */}
      <AnimatePresence mode="wait">
        <motion.section
          key={tab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.3 }}
          className="max-w-7xl mx-auto px-4 pb-16 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3"
        >
          {isLoading &&
            Array.from({ length: 8 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}

          {tab === "combos" &&
            combos?.map((c) => (
              <ComboCard
                key={c.id}
                combo={c}
                compact
                onView={() => {
                  rememberProduct("combo", c);
                  setActiveCombo(c);
                }}
              />
            ))}

          {tab === "items" &&
            items?.map((i) => (
              <ItemCardMini
                key={i.id}
                item={i}
                onView={() => {
                  rememberProduct("item", i);
                  setActiveItem(i);
                }}
              />
            ))}

          {tab === "snacks" &&
            snacks?.map((s) => (
              <SnackCard key={s.id} snack={s} />
            ))}
        </motion.section>
      </AnimatePresence>

      {/* ================= MODALS ================= */}
      {activeCombo && (
        <ProductDetailModal
          product={activeCombo}
          onClose={() => setActiveCombo(null)}
          onOpenItems={() => setShowItemList(true)}
          onOpenSnacks={() => setShowSnacks(true)}
        />
      )}

      <ItemListModal
        open={showItemList}
        items={items || []}
        onClose={() => setShowItemList(false)}
        onSelectItem={(i) => {
          rememberProduct("item", i);
          setActiveItem(i);
          setShowItemList(false);
        }}
      />

      <ItemDetailModal
        open={!!activeItem}
        item={activeItem}
        onClose={() => setActiveItem(null)}
      />

      <SnackPickerModal
        open={showSnacks}
        snacks={snacks || []}
        onClose={() => setShowSnacks(false)}
      />
    </main>
  );
}
