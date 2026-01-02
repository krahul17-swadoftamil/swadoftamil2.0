import { memo } from "react";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";

/* ======================================================
   ComboCard — Premium Breakfast Card (Aligned v2)
   Data-first • Stable layout • Conversion-safe
====================================================== */

function ComboCard({ combo, onView, compact = false }) {
  const { addCombo } = useCart();
  if (!combo) return null;

  /* ================= IMAGE ================= */
  const image = resolveMediaUrl(
    combo.primary_image ||
      combo.image ||
      combo.image_url
  );

  /* ================= DATA (BACKEND IS SOURCE) ================= */
  const name = combo.name || "Tamil Breakfast Combo";

  const description = (
    combo.description ||
    combo.short_description ||
    ""
  )
    .replace(/\r?\n/g, " • ")
    .trim();

  const price = Number(combo.selling_price || 0);

  const serves =
    combo.serve_persons ||
    combo.serves ||
    combo.serving_text ||
    null;

  const inStock =
    combo.available_quantity == null
      ? true
      : Number(combo.available_quantity) > 0;

  /* ================= QUICK ADD ================= */
  const handleQuickAdd = (e) => {
    e.stopPropagation();
    if (!inStock) return;
    addCombo(combo, 1);
  };

  /* ================= OPEN DETAIL ================= */
  const openDetail = () => {
    onView?.(combo);
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
      <div className="relative h-44 w-full bg-surface overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={`${name} – authentic Tamil breakfast`}
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
          {combo.is_featured && (
            <span className="px-2 py-1 rounded-full bg-accent text-black">
              ⭐ Best Seller
            </span>
          )}

          {serves && (
            <span className="px-2 py-1 rounded-full bg-black/60 text-white">
              🍽 Serves {serves}
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
            + Add
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
          <span className="text-accent text-lg font-bold">
            ₹{price.toFixed(0)}
          </span>

          <span
            className={`text-xs font-medium ${
              inStock
                ? "text-green-600"
                : "text-red-600"
            }`}
          >
            {inStock ? "Fresh today" : "Sold out"}
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

export default memo(ComboCard);
