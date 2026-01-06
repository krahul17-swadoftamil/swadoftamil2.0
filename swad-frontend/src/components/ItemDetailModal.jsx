import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import ItemCardMini from "./ItemCardMini";

/* ======================================================
   ItemDetailModal — Prepared Item (v2)
   • Clarity-first
   • ERP-safe
   • Lightweight
====================================================== */

export default function ItemDetailModal({ open, item, onClose }) {
  const { addItem, incItem, cart } = useCart();

  /* ================= ESC TO CLOSE ================= */
  useEffect(() => {
    if (!open) return;
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);

  if (!open || !item) return null;

  const image = resolveMediaUrl(
    item.primary_image || item.image || null
  );

  const price = Number(item.selling_price ?? item.price ?? 0);

  const portion =
    item.display_quantity && item.unit
      ? `${Math.round(item.display_quantity)} ${item.unit}`
      : null;

  // Prepared items are always available (ERP rule)
  const existing = cart.items?.find(
    (x) => String(x.id) === String(item.id)
  );
  const qty = existing?.qty || 0;

  const related = Array.isArray(item.recommended_addons)
    ? item.recommended_addons
    : [];

  /* ================= ACTION ================= */
  const handleAdd = () => {
    existing ? incItem(item.id) : addItem(item, 1);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ 
              duration: 0.3, 
              ease: "easeOut",
              scale: { type: "spring", damping: 25, stiffness: 300 }
            }}
            onClick={(e) => e.stopPropagation()}
            className="
              w-full sm:max-w-md
              bg-card rounded-t-3xl sm:rounded-2xl
              overflow-hidden flex flex-col
            "
          >
        {/* ================= HEADER ================= */}
        <div className="p-4 flex items-center justify-between border-b border-subtle">
          <h2 className="text-lg font-semibold">{item.name}</h2>
          <button
            onClick={onClose}
            className="text-muted hover:text-text"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* ================= BODY ================= */}
        <div className="p-4 space-y-4">
          {/* IMAGE (SMALL, OPTIONAL) */}
          {image && (
            <div className="h-40 bg-surface rounded-xl flex items-center justify-center">
              <img
                src={image}
                alt={item.name}
                className="max-h-full object-contain"
              />
            </div>
          )}

          {/* DESCRIPTION */}
          {item.description && (
            <p className="text-sm text-muted leading-relaxed">
              {item.description}
            </p>
          )}

          {/* META */}
          <div className="flex items-center gap-3 text-sm">
            {portion && (
              <span className="px-2 py-1 rounded bg-black/10">
                {portion}
              </span>
            )}
            <span className="text-green-500 font-medium">
              Available now
            </span>
          </div>

          {/* PRICE + ADD */}
          <div className="flex items-center justify-between pt-2">
            <div>
              <div className="text-xl font-bold text-accent">
                ₹{price}
              </div>
              <div className="text-xs text-muted">
                Prepared fresh
              </div>
            </div>

            <button
              onClick={handleAdd}
              className="px-5 py-2 rounded-xl bg-accent text-black font-semibold hover:bg-accent/90"
            >
              {qty > 0 ? `Add more (${qty})` : "Add item"}
            </button>
          </div>

          {/* ================= PAIRS WELL ================= */}
          {related.length > 0 && (
            <div className="pt-4 space-y-2">
              <div className="text-sm font-semibold">
                Pairs well with
              </div>

              <div className="grid grid-cols-2 gap-3">
                {related.map((addon) => (
                  <ItemCardMini
                    key={addon.id}
                    item={addon}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ================= FOOTER ================= */}
        <div className="border-t border-subtle p-3 text-xs text-muted text-center">
          Add-ons are optional · Items added separately
        </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
