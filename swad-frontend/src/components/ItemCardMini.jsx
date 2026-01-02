import { memo } from "react";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";

/* ======================================================
   ItemCardMini — Prepared Item (Aligned v2)
   Backend-driven • Stable layout • Combo-consistent
====================================================== */

function ItemCardMini({ item, onView }) {
  const { addItem, incItem, cart } = useCart();
  if (!item) return null;

  /* ================= IMAGE ================= */
  const image = resolveMediaUrl(
    item.primary_image ||
      item.image ||
      (Array.isArray(item.images) ? item.images[0] : null)
  );

  /* ================= DATA (DJANGO = SOURCE) ================= */
  const name = item.name || "Prepared Item";

  const description = (
    item.description ||
    item.short_description ||
    item.story ||
    ""
  )
    .replace(/\r?\n/g, " • ")
    .trim();

  const price = Number(
    item.selling_price ??
      item.price ??
      0
  );

  /* ================= PORTION ================= */
  const portion =
    item.display_quantity && item.unit
      ? `${Math.round(item.display_quantity)} ${item.unit}`
      : null;

  /* ================= STOCK ================= */
  const inStock =
    item.stock_qty == null
      ? true
      : Number(item.stock_qty) > 0;

  /* ================= CART STATE ================= */
  const existing = cart.items?.find(
    (i) => String(i.id) === String(item.id)
  );

  /* ================= QUICK ADD ================= */
  const handleQuickAdd = (e) => {
    e.stopPropagation();
    if (!inStock) return;

    existing
      ? incItem(existing.id)
      : addItem(
          {
            id: item.id,
            type: "item",
            name,
            price,
            image,
            portion,
          },
          1
        );
  };

  /* ================= OPEN DETAIL ================= */
  const openDetail = () => {
    onView?.(item);
  };

  return (
    <article
      role="button"
      tabIndex={0}
      aria-label={`View ${name}`}
      onClick={openDetail}
      onKeyDown={(e) =>
        (e.key === "Enter" || e.key === " ") && openDetail()
      }
      className="
        group relative cursor-pointer
        rounded-3xl overflow-hidden
        bg-card border border-subtle
        transition-all duration-300
        hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(0,0,0,0.25)]
        focus:outline-none focus:ring-2 focus:ring-accent/40
        flex flex-col h-full
      "
    >
      {/* ================= IMAGE ================= */}
      <div className="relative h-40 w-full bg-surface overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={`${name} – freshly prepared`}
            loading="lazy"
            className="
              w-full h-full object-cover
              transition-transform duration-500
              group-hover:scale-105
            "
          />
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-muted">
            Image coming soon
          </div>
        )}

        {/* BADGES */}
        <div className="absolute top-3 left-3 flex gap-2 text-[10px] font-semibold">
          <span className="px-2 py-1 rounded-full bg-black/60 text-white">
            🍳 Fresh
          </span>

          {portion && (
            <span className="px-2 py-1 rounded-full bg-black/60 text-white">
              📏 {portion}
            </span>
          )}
        </div>

        {/* QUICK ADD */}
        {inStock && (
          <button
            onClick={handleQuickAdd}
            className="
              absolute bottom-3 right-3
              px-4 py-1.5
              rounded-full text-xs font-semibold
              bg-accent text-black
              shadow-lg
              opacity-0 group-hover:opacity-100
              transition-opacity
            "
            aria-label={`Quick add ${name}`}
          >
            {existing ? "＋ Add more" : "+ Add"}
          </button>
        )}
      </div>

      {/* ================= CONTENT ================= */}
      <div className="p-4 flex flex-col flex-1">
        {/* TITLE */}
        <h3 className="text-base font-semibold leading-snug line-clamp-2">
          {name}
        </h3>

        {/* DESCRIPTION */}
        {description && (
          <p className="text-xs text-muted mt-1 line-clamp-2">
            {description}
          </p>
        )}

        {/* PRICE — PINNED */}
        <div className="mt-auto pt-3 flex items-center justify-between">
          {price > 0 ? (
            <span className="text-accent text-lg font-bold">
              ₹{price.toFixed(0)}
            </span>
          ) : (
            <span className="text-xs text-neutral-400">
              Included in combos
            </span>
          )}

          <span
            className={`text-xs font-medium ${
              inStock
                ? "text-green-600"
                : "text-red-600"
            }`}
          >
            {inStock ? "Available" : "Sold out"}
          </span>
        </div>
      </div>

      {/* SOLD OUT OVERLAY */}
      {!inStock && (
        <div className="absolute inset-0 bg-black/55 flex items-center justify-center text-white text-sm font-semibold">
          Sold Out
        </div>
      )}
    </article>
  );
}

export default memo(ItemCardMini);
