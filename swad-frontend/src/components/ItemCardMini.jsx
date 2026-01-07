import { memo } from "react";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import LazyImage from "./LazyImage";

/* ======================================================
   ItemCard — Clean Prepared Item (v5)
   • Matches ComboCard & SnackCard
   • Simple add flow
   • No visual noise
====================================================== */

function ItemCard({ item, onView, featured = false }) {
  const { incItem, addItem, cart } = useCart();

  if (!item) return null;

  /* ================= DATA ================= */
  const image = resolveMediaUrl(
    item.image_url ||
      item.primary_image ||
      item.image ||
      (Array.isArray(item.images) ? item.images[0] : null)
  );

  const name = item.name || "Prepared Item";

  const description = (
    item.short_description ||
    item.description ||
    item.story ||
    ""
  )
    .replace(/\r?\n/g, " • ")
    .trim();

  const price = Number(item.selling_price ?? item.price ?? 0);

  const portion =
    item.display_quantity && item.unit
      ? `${Math.round(item.display_quantity)} ${item.unit}`
      : null;

  // Prepared items are always available (ERP rule)
  const inStock = true;

  const existing = cart.items?.find(
    (x) => String(x.id) === String(item.id)
  );
  const qty = existing?.qty || 0;

  /* ================= ACTIONS ================= */
  const handleAdd = (e) => {
    e.stopPropagation();
    existing ? incItem(item.id) : addItem(item, 1);
  };

  const handleView = () => {
    onView?.(item);
  };

  /* ================= UI ================= */
  return (
    <article
      role="button"
      tabIndex={0}
      onClick={handleView}
      onKeyDown={(e) =>
        (e.key === "Enter" || e.key === " ") && handleView()
      }
      aria-label={`View ${name}`}
      className={`
        relative flex flex-col overflow-hidden
        rounded-2xl bg-card border border-subtle
        transition-all duration-200
        hover:shadow-lg hover:-translate-y-0.5
        focus:outline-none focus:ring-2 focus:ring-accent/40
        ${featured ? "ring-2 ring-accent/30" : ""}
      `}
    >
      {/* ================= IMAGE ================= */}
      <div className="relative aspect-[4/3] bg-surface overflow-hidden">
        {image ? (
          <LazyImage
            src={image}
            alt={name}
            className="w-full h-full object-cover object-center"
          />
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-muted">
            Image coming soon
          </div>
        )}

        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/35" />

        {/* BADGES */}
        <div className="absolute top-3 left-3 flex gap-2 text-[11px] font-semibold">
          {portion && (
            <span className="px-2 py-1 rounded-full bg-black/60 text-white">
              {portion}
            </span>
          )}
        </div>

        {/* PRICE */}
        {price > 0 && (
          <div className="absolute bottom-3 left-3 bg-black/70 text-white px-3 py-1.5 rounded-full text-base font-bold">
            ₹{price.toFixed(0)}
          </div>
        )}

        {/* ADD BUTTON */}
        <div className="absolute bottom-3 right-3">
          <div className="bg-black/60 backdrop-blur-sm rounded-full px-1 py-1 transition-all duration-200 group">
            <button
              onClick={handleAdd}
              className="
                px-3 py-1.5 rounded-full
                text-xs font-semibold
                bg-accent text-black
                hover:bg-accent/90
                transition-all duration-200
                group-hover:px-5
                relative overflow-hidden
              "
            >
              <span className="transition-all duration-200 group-hover:opacity-0">
                {qty > 0 ? `+ ${qty}` : "Add"}
              </span>
              <span className="absolute inset-0 flex items-center justify-center opacity-0 transition-all duration-200 group-hover:opacity-100">
                {qty > 0 ? `+ ${qty}` : "Add +"}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* ================= CONTENT ================= */}
      <div className="p-4 flex flex-col flex-1">
        <h3 className="text-sm font-semibold leading-snug line-clamp-2">
          {name}
        </h3>

        {description && (
          <p className="text-xs text-muted mt-2 line-clamp-2">
            {description}
          </p>
        )}

        <div className="mt-auto pt-4 flex items-center justify-between text-xs">
          <span className="text-green-500">Available today</span>
        </div>
      </div>
    </article>
  );
}

export default memo(ItemCard);
