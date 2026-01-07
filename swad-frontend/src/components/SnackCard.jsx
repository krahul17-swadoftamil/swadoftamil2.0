import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import { useEngagement } from "../hooks/useEngagement";
import { usePersonalization } from "../hooks/usePersonalization";
import LazyImage from "./LazyImage";

/* ======================================================
   SnackCard — Muted, Secondary Add-on (v5)
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
        rounded-lg bg-surface border border-subtle/50
        transition-all duration-200
        hover:shadow-sm hover:border-subtle
        focus:outline-none focus:ring-1 focus:ring-accent/30
        ${featured ? "ring-1 ring-accent/20" : ""}
      `}
    >
      {/* ================= IMAGE ================= */}
      <div className="relative aspect-square bg-muted/20 overflow-hidden">
        {image ? (
          <>
            <img
              src={image}
              alt={name}
              className="w-full h-full object-cover object-center filter brightness-110 contrast-105 saturate-110"
              loading="lazy"
            />
            
            {/* Premium Lighting - Top Light */}
            <div className="absolute inset-0 bg-gradient-to-b from-white/12 via-transparent to-transparent pointer-events-none" />
            
            {/* Premium Lighting - Side Light */}
            <div className="absolute inset-0 bg-gradient-to-r from-white/8 via-transparent to-black/10 pointer-events-none" />
            
            {/* Premium Lighting - Bottom Shadow */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/30 pointer-events-none" />
            
            {/* Soft Vignette */}
            <div className="absolute inset-0 pointer-events-none" style={{
              background: 'radial-gradient(ellipse at center, transparent 20%, rgba(0,0,0,0.2) 100%)'
            }} />
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-muted">
            Image coming soon
          </div>
        )}

        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/20" />

        {/* BADGES - SMALLER */}
        <div className="absolute top-2 left-2 flex gap-1 text-[10px] font-medium">
          {badge && (
            <span className="px-1.5 py-0.5 rounded bg-accent/90 text-black">
              {badge}
            </span>
          )}
          <span className="px-1.5 py-0.5 rounded bg-black/40 text-white/80">
            Add-on
          </span>
        </div>

        {/* PRICE - SMALLER */}
        <div className="absolute bottom-2 left-2 bg-black/50 text-white/90 px-2 py-1 rounded text-xs font-medium">
          ₹{price.toFixed(0)}
        </div>

        {/* ADD BUTTON - SMALLER */}
        <div className="absolute bottom-2 right-2">
          <button
            onClick={handleAdd}
            className="
              px-2 py-1 rounded text-xs font-medium
              bg-accent/90 text-black
              hover:bg-accent
              transition-all duration-200
              relative overflow-hidden
            "
          >
            {qty > 0 ? `+ ${qty}` : (snack.min_order_qty > 1 ? `Add ${snack.min_order_qty}` : "Add")}
          </button>
        </div>
      </div>

      {/* ================= CONTENT - SMALLER ================= */}
      <div className="p-3 flex flex-col flex-1">
        <h3 className="text-xs font-medium leading-tight line-clamp-2 text-muted-foreground">
          {name}
        </h3>

        {description && (
          <p className="text-xs text-muted mt-1 line-clamp-1">
            {description}
          </p>
        )}

        {/* EXPIRY DATE - SMALLER */}
        {snack.expiry_date && (
          <div className="mt-1 text-xs text-green-600/70">
            Best before: {formatExpiryDate(snack.expiry_date)}
          </div>
        )}

        {/* PAIRING SUGGESTIONS - SMALLER */}
        {snack.pairs_with && snack.pairs_with.length > 0 && (
          <div className="mt-1 text-xs text-blue-600/70">
            Pairs with {formatPairings(snack.pairs_with)}
          </div>
        )}

        <div className="mt-auto pt-2 space-y-1">
          {/* RATING - SMALLER */}
          {rating > 4.2 && (
            <div className="flex items-center gap-1">
              <span className="text-yellow-400 text-xs">⭐</span>
              <span className="text-xs text-muted">{rating.toFixed(1)}</span>
            </div>
          )}

          {/* FOOTER - SMALLER */}
          <div className="flex justify-between items-center text-xs text-muted/60">
            <span>Optional</span>
            {snack.region && snack.region !== "other" && (
              <span className="text-accent/70">
                {snack.region.charAt(0).toUpperCase() + snack.region.slice(1).replace('_', ' ')}
              </span>
            )}
          </div>

          {/* MIN ORDER RULE - SMALLER */}
          {snack.min_order_qty > 1 && (
            <div className="text-xs text-orange-600/70">
              Min {snack.min_order_qty} packs
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

export default memo(SnackCard);
