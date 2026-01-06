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
      tabIndex={0}
      onClick={handleView}
      onKeyDown={(e) =>
        (e.key === "Enter" || e.key === " ") && handleView()
      }
      aria-label={`View ${name}`}
      className={`
        relative flex flex-col overflow-hidden
        rounded-2xl bg-card border border-subtle
        focus:outline-none focus:ring-2 focus:ring-accent/40
        ${pressed ? "scale-[0.98]" : ""}
        ${featured ? "ring-2 ring-accent/30" : ""}
        ${size === "large" ? "transform scale-110" : ""}
      `}
      whileHover={{ y: -4, scale: size === "large" ? 1.02 : 1.02 }}
      transition={{ type: "spring", stiffness: 200, damping: 26 }}
    >
      {/* ================= IMAGE ================= */}
      <div className={`relative ${imageSizeClasses[size]} bg-surface overflow-hidden`}>
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

        {/* BADGES - MAX 2 WITH PRIORITY */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2 text-[11px] font-semibold">
          {/* Priority 1: Serves X (only if serves exists) */}
          {serves && (
            <span className="px-2 py-1 rounded-full bg-black/60 text-white">
              Serves {serves}
            </span>
          )}
        </div>

        {/* PRICE - BOTTOM LEFT */}
        <div className="absolute bottom-3 left-3 bg-black/70 text-white px-3 py-1.5 rounded-full text-sm font-bold">
          ₹{price.toFixed(0)}
        </div>

        {/* ADD BUTTON */}
        {inStock && (
          <motion.div
            className="absolute bottom-3 right-3"
            animate={bounce ? { scale: [1, 1.15, 0.95, 1] } : { scale: 1 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            <div className="bg-black/60 backdrop-blur-sm rounded-full px-1 py-1 transition-all duration-200 group">
              <button
                onClick={handleAdd}
                className="
                  px-3 py-1.5 rounded-full text-xs font-semibold
                  bg-accent text-black
                  hover:bg-accent/90
                  transition-all duration-200
                  group-hover:px-5
                "
              >
                {qty > 0 ? `+ ${qty}` : "Add Breakfast"}
              </button>
            </div>
          </motion.div>
        )}
      </div>

      {/* ================= CONTENT ================= */}
      <div className="p-4 flex flex-col flex-1">
        {/* COMBO NAME */}
        <h3 className={`${size === "large" ? "text-xl" : "text-lg"} font-bold leading-snug line-clamp-2 mb-2`}>
          {name}
        </h3>

        {/* WHY THIS COMBO */}
        <p className={`${size === "large" ? "text-base" : "text-sm"} text-accent font-medium mb-4`}>
          {serves ? `Perfect for ${serves} people` : 
           total_items >= 3 ? "Complete snack assortment" : 
           "Traditional South Indian flavors"}
        </p>

        {/* PRICE & ADD BUTTON */}
        <div className="mt-auto flex items-center justify-between">
          <div className={`${size === "large" ? "text-2xl" : "text-xl"} font-bold text-accent`}>
            ₹{price.toFixed(0)}
          </div>
        </div>
      </div>

      {/* SOLD OUT */}
      {!inStock && (
        <div className="absolute inset-0 bg-black/70 flex items-center justify-center text-white text-sm font-semibold rounded-2xl">
          Sold Out
        </div>
      )}
    </motion.article>
  );
}

export default memo(ComboCard);
