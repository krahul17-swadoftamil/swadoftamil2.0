import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useCart } from "../context/CartContext";

/* ======================================================
   FloatingCart — Slide-up Drawer (Swiggy/Zomato Style)
====================================================== */

export default function FloatingCart() {
  /* ================= CONTEXT ================= */

  const {
    cart,
    itemCount,
    total,

    incItem,
    decItem,
    removeItem,

    incCombo,
    decCombo,
    removeCombo,

    incSnack,
    decSnack,
    removeSnack,

    openCheckout,
  } = useCart();

  /* ================= DRAWER STATE ================= */

  const [isOpen, setIsOpen] = useState(false);

  /* ================= NORMALIZE ROWS ================= */

  const rows = useMemo(() => {
    return [
      ...(cart.combos || []).map((c) => ({ ...c, type: "combo" })),
      ...(cart.items || []).map((i) => ({ ...i, type: "item" })),
      ...(cart.snacks || []).map((s) => ({ ...s, type: "snack" })),
    ];
  }, [cart]);

  /* ================= ACTION ROUTER ================= */

  const inc = (x) => {
    if (x.type === "combo") incCombo(x.id);
    if (x.type === "item") incItem(x.id);
    if (x.type === "snack") incSnack(x.id);
  };

  const dec = (x) => {
    if (x.type === "combo") decCombo(x.id);
    if (x.type === "item") decItem(x.id);
    if (x.type === "snack") decSnack(x.id);
  };

  const remove = (x) => {
    if (x.type === "combo") removeCombo(x.id);
    if (x.type === "item") removeItem(x.id);
    if (x.type === "snack") removeSnack(x.id);
  };

  /* ================= RENDER ================= */

  if (itemCount === 0) return null;

  return (
    <>
      {/* BACKDROP */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/50 z-40"
          />
        )}
      </AnimatePresence>

      {/* DRAWER */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-card rounded-t-3xl shadow-2xl max-h-[80vh] overflow-hidden"
          >
            {/* HANDLE */}
            <div className="flex justify-center py-3">
              <div className="w-12 h-1.5 bg-subtle rounded-full" />
            </div>

            {/* HEADER */}
            <div className="px-6 pb-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold">Your Cart ({itemCount})</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-muted hover:text-text p-1"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* ITEMS */}
            <div className="flex-1 overflow-y-auto px-6 max-h-96">
              <div className="space-y-4">
                {rows.map((x) => (
                  <div
                    key={`${x.type}-${x.id}`}
                    className="flex justify-between items-center gap-4 p-3 bg-surface rounded-xl"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">
                        {x.name}
                      </div>
                      <div className="text-xs text-muted">
                        ₹{x.price} each
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => dec(x)}
                          className="w-8 h-8 rounded-full bg-accent/10 hover:bg-accent/20 flex items-center justify-center text-sm font-semibold transition-colors"
                        >
                          −
                        </button>
                        <span className="font-semibold w-6 text-center">{x.qty}</span>
                        <button
                          onClick={() => inc(x)}
                          className="w-8 h-8 rounded-full bg-accent/10 hover:bg-accent/20 flex items-center justify-center text-sm font-semibold transition-colors"
                        >
                          +
                        </button>
                      </div>
                      <button
                        onClick={() => remove(x)}
                        className="text-muted hover:text-red-400 p-1"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* FOOTER */}
            <div className="p-6 border-t border-subtle bg-surface/50">
              <div className="flex justify-between font-bold text-lg mb-4">
                <span>Total</span>
                <span>₹{total}</span>
              </div>

              <button
                onClick={() => {
                  setIsOpen(false);
                  openCheckout();
                }}
                className="w-full py-4 rounded-xl bg-accent text-black font-bold text-lg shadow-lg hover:shadow-xl transition-shadow"
              >
                Proceed to Checkout →
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* FLOATING CART BUTTON */}
      <AnimatePresence>
        {!isOpen && itemCount > 0 && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-30 flex items-center gap-3 px-4 py-3 rounded-full bg-accent text-black font-semibold shadow-2xl"
          >
            {/* CART ICON */}
            <span className="text-lg">🛒</span>

            {/* ITEM COUNT BADGE */}
            <span className="h-6 w-6 rounded-full bg-black/20 flex items-center justify-center text-xs font-bold">
              {itemCount}
            </span>

            {/* TOTAL */}
            <span className="text-sm font-semibold">
              ₹{total}
            </span>
          </motion.button>
        )}
      </AnimatePresence>
    </>
  );
}
