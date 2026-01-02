import { memo, useEffect, useState } from "react";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";

/* ======================================================
   SnackCard — Add-on Card (Aligned v2)
   Stable layout • Cart-aware • No mis-clicks
====================================================== */

function SnackCard({ snack, onView }) {
  const {
    addSnack,
    openCheckout,
    cart,
  } = useCart();

  const [justAdded, setJustAdded] = useState(false);
  if (!snack) return null;

  /* ================= IMAGE ================= */
  const image = resolveMediaUrl(
    snack.animated_image ||
      snack.primary_image ||
      snack.image ||
      snack.image_url
  );

  /* ================= DATA (DJANGO ONLY) ================= */
  const name = snack.name || "Snack";
  const description =
    snack.short_description ||
    snack.description ||
    snack.story ||
    "";

  const price = Number(snack.selling_price ?? snack.price ?? 0);

  const isBest =
    snack.is_best_seller ||
    snack.is_popular ||
    false;

  /* ================= CART STATE ================= */
  const existing = cart.snacks?.find(
    (s) => String(s.id) === String(snack.id)
  );

  /* ================= QUICK ADD ================= */
  const handleQuickAdd = (e) => {
    e.preventDefault();
    e.stopPropagation();

    addSnack(snack, 1);

    // Visual feedback
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 900);

    // Auto-open checkout on first snack only
    if (!existing) {
      openCheckout?.();
    }
  };

  /* ================= OPEN DETAIL ================= */
  const openDetail = () => {
    onView?.(snack);
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
            alt={name}
            loading="lazy"
            className="
              w-full h-full object-contain
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
          {isBest && (
            <span className="px-2 py-1 rounded-full bg-black/60 text-white">
              ⭐ Popular
            </span>
          )}
          <span className="px-2 py-1 rounded-full bg-black/60 text-white">
            🍽 Add-on
          </span>
        </div>

        {/* QUICK ADD */}
        <button
          type="button"
          onClick={handleQuickAdd}
          className={`
            absolute bottom-3 right-3
            px-4 py-1.5 rounded-full
            text-xs font-semibold
            bg-accent text-black
            shadow-lg
            transition-all
            ${
              justAdded
                ? "scale-110 ring-2 ring-accent/40"
                : "opacity-0 group-hover:opacity-100"
            }
          `}
          aria-label={`Quick add ${name}`}
        >
          {existing ? "✓ Added" : "+ Add"}
        </button>
      </div>

      {/* ================= CONTENT ================= */}
      <div className="p-4 flex flex-col flex-1">
        {/* NAME */}
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

          <span className="text-xs text-neutral-400">
            Breakfast add-on
          </span>
        </div>
      </div>
    </article>
  );
}

export default memo(SnackCard);
