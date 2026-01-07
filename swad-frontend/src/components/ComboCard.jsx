import { memo, useState } from "react";
import { motion } from "framer-motion";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import { useEngagement } from "../hooks/useEngagement";
import { usePersonalization } from "../hooks/usePersonalization";
import LazyImage from "./LazyImage";

/* ======================================================
   ComboCard — Premium, Calm, Food-First (v6)
====================================================== */

function ComboCard({
  combo,
  combos = [],
  onView,
  onRequireAuth,
  isAuthenticated = false,
  badge = null,
  featured = false,
  size = "normal",
}) {
  const { cart, addCombo, incCombo } = useCart();
  const [pressed, setPressed] = useState(false);
  const [bounce, setBounce] = useState(false);

  const { rating } = useEngagement(combo?.id, "combo");

  const { trackView, trackClick } = usePersonalization();

  // Size variants
  const sizeClasses = {
    normal: "text-lg",
    large: "text-xl scale-110",
  };

  const imageSizeClasses = {
    normal: "aspect-[5/4]",
    large: "aspect-[5/4]",
  };

  if (!combo) return null;

  /* ================= DATA ================= */
  const image = resolveMediaUrl(
    combo.image_url || combo.primary_image || combo.image
  );

  const name = combo.name || "Tamil Breakfast Combo";

  const price = Number(combo.selling_price || 0);

  const serves =
    combo.serve_persons ||
    combo.serves ||
    combo.serving_text ||
    null;

  const total_items = Number(combo.total_items || 0);

  const inStock =
    combo.available_quantity == null
      ? true
      : Number(combo.available_quantity) > 0;

  const existing = cart.combos.find((c) => c.id === combo.id);
  const qty = existing?.qty || 0;

  /* ================= ACTIONS ================= */
  const handleAdd = (e) => {
    e.stopPropagation();
    if (!inStock) return;

    // Check authentication - show contextual sign-in if not authenticated
    if (!isAuthenticated) {
      onRequireAuth?.();
      return;
    }

    existing ? incCombo(combo.id) : addCombo(combo, 1);
    trackClick(combo.id, "combo");
    
    // Trigger bounce animation
    setBounce(true);
    setTimeout(() => setBounce(false), 600);
  };

  const handleView = () => {
    trackView(combo.id, "combo");
    setPressed(true);
    setTimeout(() => {
      setPressed(false);
      onView?.(combo);
    }, 90);
  };

  /* ================= UI ================= */
  return (
    <motion.article
      role="button"
      tabIndex={inStock ? 0 : -1}
      onClick={inStock ? handleView : undefined}
      onKeyDown={(e) =>
        inStock && (e.key === "Enter" || e.key === " ") && handleView()
      }
      aria-label={inStock ? `View ${name}` : `${name} - Tomorrow morning`}
      className={`
        relative flex flex-col overflow-hidden
        rounded-2xl bg-card border border-subtle
        focus:outline-none focus:ring-2 focus:ring-accent/40
        ${pressed ? "scale-[0.98]" : ""}
        ${featured ? "ring-2 ring-accent/30" : ""}
        ${size === "large" ? "transform scale-110" : ""}
        ${!inStock ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}
      `}
      whileHover={inStock ? { y: -4, scale: size === "large" ? 1.02 : 1.02 } : {}}
      transition={{ type: "spring", stiffness: 200, damping: 26 }}
    >
      {/* ================= IMAGE (HERO) ================= */}
      <div className={`relative ${imageSizeClasses[size]} bg-surface overflow-hidden`}>
        {image ? (
          <>
            <img
              src={image}
              alt={name}
              className="w-full h-full object-cover object-center filter brightness-110 contrast-105"
              loading="lazy"
            />
            {/* Premium Lighting Layer - Top Light */}
            <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />
            
            {/* Premium Lighting Layer - Bottom Shadow */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/25 pointer-events-none" />
            
            {/* Vignette Effect */}
            <div className="absolute inset-0 pointer-events-none" style={{
              background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.15) 100%)'
            }} />
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-muted">
            Image coming soon
          </div>
        )}
      </div>

      {/* ================= CONTENT ================= */}
      <div className="p-4 flex flex-col flex-1">
        {/* COMBO NAME */}
        <h3 className={`${size === "large" ? "text-xl" : "text-lg"} font-bold leading-snug line-clamp-2 mb-3`}>
          {name}
        </h3>

        {/* PRICE */}
        <div className={`${size === "large" ? "text-2xl" : "text-xl"} font-bold text-accent mb-2`}>
          ₹{price.toFixed(0)}
        </div>

        {/* SERVES COUNT */}
        {serves && (
          <div className="text-sm text-muted font-medium mb-4">
            Serves {serves}
          </div>
        )}

        {/* CTA BUTTON */}
        <div className="mt-auto">
          {inStock ? (
            <motion.button
              onClick={handleAdd}
              className="
                w-full py-3 px-4 rounded-xl text-sm font-semibold
                bg-accent text-black
                hover:bg-accent/90
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-accent/40
              "
              animate={bounce ? { scale: [1, 1.05, 0.98, 1] } : { scale: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              {qty > 0 ? `Add More (${qty})` : "Add Breakfast"}
            </motion.button>
          ) : (
            <div className="w-full py-3 px-4 rounded-xl text-sm font-semibold bg-muted text-muted-foreground text-center">
              Tomorrow morning
            </div>
          )}
        </div>
      </div>
    </motion.article>
  );
}

export default memo(ComboCard);
