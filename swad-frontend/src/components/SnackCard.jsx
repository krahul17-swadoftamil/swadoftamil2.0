import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import { useEngagement } from "../hooks/useEngagement";
import { usePersonalization } from "../hooks/usePersonalization";
import LazyImage from "./LazyImage";

/* ======================================================
   SnackCard — Calm, Premium Add-on (v4)
====================================================== */

function SnackCard({
  snack,
  onView,
  badge = null,
  featured = false,
}) {
  const { addSnack, incSnack, cart } = useCart();

  const { rating } = useEngagement(snack?.id, "snack");

  const { trackView, trackClick } = usePersonalization();

  if (!snack) return null;

  /* ================= DATA ================= */
  const image = resolveMediaUrl(
    snack.animated_image ||
      snack.primary_image ||
      snack.image ||
      snack.image_url
  );

  const name = snack.name || "Snack";

  const description = useMemo(
    () =>
      (
        snack.short_description ||
        snack.description ||
        snack.story ||
        ""
      )
        .replace(/\r?\n/g, " • ")
        .trim(),
    [snack]
  );

  const price = Number(snack.selling_price ?? snack.price ?? 0);

  const existing = cart.snacks?.find(
    (x) => String(x.id) === String(snack.id)
  );
  const qty = existing?.qty || 0;

  /* ================= UTILITIES ================= */
  const formatExpiryDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', { 
      day: 'numeric', 
      month: 'short',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
    });
  };

  const formatPairings = (pairs) => {
    if (!pairs || pairs.length === 0) return "";
    if (pairs.length === 1) return pairs[0];
    if (pairs.length === 2) return `${pairs[0]} & ${pairs[1]}`;
    return `${pairs.slice(0, -1).join(", ")} & ${pairs[pairs.length - 1]}`;
  };

  /* ================= ACTIONS ================= */
  const handleAdd = (e) => {
    e.stopPropagation();
    const minQty = snack.min_order_qty || 1;
    if (existing) {
      incSnack(snack.id);
    } else {
      // Add minimum quantity for first addition
      addSnack(snack, minQty);
    }
    trackClick(snack.id, "snack");
  };

  const handleView = () => {
    trackView(snack.id, "snack");
    onView?.(snack);
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
          {badge && (
            <span className="px-2 py-1 rounded-full bg-accent text-black">
              {badge}
            </span>
          )}
          <span className="px-2 py-1 rounded-full bg-black/60 text-white">
            Add-on
          </span>
        </div>

        {/* PRICE */}
        <div className="absolute bottom-3 left-3 bg-black/70 text-white px-3 py-1.5 rounded-full text-sm font-bold">
          ₹{price.toFixed(0)} · {snack.pack_size || '200g'} · Handmade
        </div>

        {/* ADD BUTTON */}
        <div className="absolute bottom-3 right-3">
          <div className="bg-black/60 backdrop-blur-sm rounded-full px-1 py-1 transition-all duration-200 group">
            <button
              onClick={handleAdd}
              className="
                px-3 py-1.5 rounded-full text-xs font-semibold
                bg-accent text-black
                hover:bg-accent/90
                transition-all duration-200
                group-hover:px-5
                relative overflow-hidden
              "
            >
              <span className="transition-all duration-200 group-hover:opacity-0">
                {qty > 0 ? `+ ${qty}` : (snack.min_order_qty > 1 ? `Add ${snack.min_order_qty}` : "Add")}
              </span>
              <span className="absolute inset-0 flex items-center justify-center opacity-0 transition-all duration-200 group-hover:opacity-100">
                {qty > 0 ? `+ ${qty}` : (snack.min_order_qty > 1 ? `Add ${snack.min_order_qty}+` : "Add +")}
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

        {/* EXPIRY DATE */}
        {snack.expiry_date && (
          <div className="mt-2 text-xs text-green-600 font-medium">
            Best before: {formatExpiryDate(snack.expiry_date)}
          </div>
        )}

        {/* PAIRING SUGGESTIONS */}
        {snack.pairs_with && snack.pairs_with.length > 0 && (
          <div className="mt-2 text-xs text-blue-600 font-medium">
            Pairs best with {formatPairings(snack.pairs_with)}
          </div>
        )}

        <div className="mt-auto pt-4 space-y-2">
          {/* RATING (only if excellent) */}
          {rating > 4.2 && (
            <div className="flex items-center gap-1">
              <span className="text-yellow-400 text-xs">⭐</span>
              <span className="text-xs text-muted">{rating.toFixed(1)}</span>
            </div>
          )}

          {/* FOOTER */}
          <div className="flex justify-between items-center text-xs text-muted">
            <span>Optional add-on</span>
            {snack.region && snack.region !== "other" && (
              <span className="text-accent font-medium">
                {snack.region.charAt(0).toUpperCase() + snack.region.slice(1).replace('_', ' ')}
              </span>
            )}
          </div>

          {/* MIN ORDER RULE */}
          {snack.min_order_qty > 1 && (
            <div className="text-xs text-orange-600 font-medium">
              Minimum {snack.min_order_qty} packs required for delivery
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

export default memo(SnackCard);
