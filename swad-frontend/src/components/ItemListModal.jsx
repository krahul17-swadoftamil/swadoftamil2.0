import { useEffect } from "react";
import ItemCardMini from "./ItemCardMini";

/* ======================================================
   ItemListModal — Prepared Items (Add-ons)
   • Shows items used in combo
   • Allows adding extra items
   • Click → opens ItemDetailModal
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

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="
          w-full sm:max-w-3xl
          bg-card rounded-t-3xl sm:rounded-2xl
          overflow-hidden
          flex flex-col
        "
      >
        {/* ================= HEADER ================= */}
        <div className="flex items-center justify-between p-4 border-b border-subtle">
          <h3 className="text-lg font-semibold">
            Available items
          </h3>
          <button
            onClick={onClose}
            className="text-muted hover:text-text"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* ================= CONTENT ================= */}
        <div className="p-4 grid grid-cols-2 sm:grid-cols-3 gap-4 overflow-y-auto">
          {items.length === 0 ? (
            <div className="col-span-full text-center text-muted text-sm">
              No items available
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
          Extra items are added separately · Combo remains unchanged
        </div>
      </div>
    </div>
  );
}
