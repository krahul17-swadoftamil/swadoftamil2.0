import { useEffect } from "react";
import { useCart } from "../context/CartContext";
import ItemCardMini from "./ItemCardMini";
import { resolveMediaUrl } from "../utils/media";

/* ======================================================
   ItemDetailModal — Prepared Item + Related Add-ons
   • Focused item view
   • Guided upsell
   • ERP-safe (separate cart lines)
====================================================== */

export default function ItemDetailModal({
  open,
  item,
  onClose,
}) {
  const { addItem } = useCart();

  /* ================= ESC TO CLOSE ================= */
  useEffect(() => {
    if (!open) return;
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);

  if (!open || !item) return null;

  const image = resolveMediaUrl(item.image);
  const price = Number(item.selling_price || 0);
  const unitLabel =
    item.unit === "ml" ? "ml" :
    item.unit === "pc" ? "pc" : "";

  const related = Array.isArray(item.recommended_addons)
    ? item.recommended_addons
    : [];

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="
          w-full sm:max-w-lg
          bg-card rounded-t-3xl sm:rounded-2xl
          overflow-hidden flex flex-col
        "
      >
        {/* ================= IMAGE ================= */}
        <div className="h-56 bg-surface flex items-center justify-center">
          {image && (
            <img
              src={image}
              alt={item.name}
              className="max-h-full p-4 object-contain"
            />
          )}
        </div>

        {/* ================= CONTENT ================= */}
        <div className="p-5 space-y-4 flex-1">
          {/* HEADER */}
          <div className="flex justify-between items-start">
            <h2 className="text-xl font-bold">{item.name}</h2>
            <button
              onClick={onClose}
              className="text-muted hover:text-text"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* DESCRIPTION */}
          {item.description && (
            <p className="text-sm text-muted leading-relaxed">
              {item.description}
            </p>
          )}

          {/* PRICE */}
          <div className="flex items-end gap-2">
            <span className="text-2xl font-bold text-accent">
              ₹{price}
            </span>
            {unitLabel && (
              <span className="text-xs text-muted">
                per {unitLabel}
              </span>
            )}
          </div>

          {/* ADD ITEM */}
          <button
            onClick={() => addItem(item)}
            disabled={!item.in_stock}
            className="btn-primary w-full"
          >
            {item.in_stock ? "Add item" : "Out of stock"}
          </button>

          {/* ================= RELATED ADD-ONS ================= */}
          {related.length > 0 && (
            <div className="pt-4 space-y-3">
              <div className="font-semibold text-sm">
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
          Extra items are added separately · Combo remains unchanged
        </div>
      </div>
    </div>
  );
}
