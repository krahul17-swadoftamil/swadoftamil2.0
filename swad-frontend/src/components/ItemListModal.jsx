import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ItemCardMini from "./ItemCardMini";

/* ======================================================
   ItemListModal — Extra Prepared Items (v2)
   • Combo helper drawer
   • Focused upsell
   • Lightweight
====================================================== */

export default function ItemListModal({
  open,
  onClose,
  items = [],
  onSelectItem,
}) {
  /* ================= ESC TO CLOSE ================= */
  useEffect(() => {
    if (!open) return;
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);

  if (!open) return null; // Keep for now

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
              w-full sm:max-w-xl
              bg-card rounded-t-3xl sm:rounded-2xl
              overflow-hidden flex flex-col
            "
          >
        {/* ================= HEADER ================= */}
        <div className="p-4 border-b border-subtle">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              Add something extra
            </h3>
            <button
              onClick={onClose}
              className="text-muted hover:text-text"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
          <p className="text-xs text-muted mt-1">
            These items will be added separately to your order
          </p>
        </div>

        {/* ================= CONTENT ================= */}
        <div className="p-4 grid grid-cols-2 gap-4 overflow-y-auto">
          {items.length === 0 ? (
            <div className="col-span-full text-center text-muted text-sm py-8">
              No extra items available
            </div>
          ) : (
            items.map((item) => (
              <ItemCardMini
                key={item.id}
                item={item}
                onView={() => onSelectItem?.(item)}
              />
            ))
          )}
        </div>

        {/* ================= FOOTER ================= */}
        <div className="border-t border-subtle p-3 text-xs text-muted text-center">
          Combo remains unchanged · Items added individually
        </div>
        </motion.div>
      </motion.div>
    )}
    </AnimatePresence>
  );
}
