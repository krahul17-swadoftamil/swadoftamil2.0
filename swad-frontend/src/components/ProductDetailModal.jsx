import { useEffect, useState } from "react";
import {
  motion,
  AnimatePresence,
  useReducedMotion,
} from "framer-motion";

/* ================= SUPPRESS FRAMER MOTION WARNING ================= */
const originalWarn = console.warn;
console.warn = (...args) => {
  if (args[0]?.includes?.("You have Reduced Motion enabled")) {
    return; // Suppress this specific warning
  }
  originalWarn(...args);
};

import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import { ChevronDown, ChevronRight } from "lucide-react";

/* ======================================================
   ProductDetailModal — Combo Detail Screen (5-second understanding)
   Rules:
   • Hero image (large, 4:3, edge-to-edge)
   • Combo name (H1) + emotional line
   • What's inside (icons + quantity)
   • Serves X + Calories (future-ready)
   • Sticky bottom bar
   • Bullet point description
   • Fresh today highlight
====================================================== */

export default function ProductDetailModal({
  product,
  onClose,
}) {
  const { addCombo, openCheckout } = useCart();
  const reduceMotion = useReducedMotion();

  const [qty, setQty] = useState(1);
  const [expandedItems, setExpandedItems] = useState(new Set());

  /* ================= ESC CLOSE ================= */
  useEffect(() => {
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  if (!product) return null;

  const isCombo = Array.isArray(product.items);

  /* ================= IMAGE ================= */
  const image = resolveMediaUrl(
    product.primary_image ||
      product.image ||
      (Array.isArray(product.images) ? product.images[0] : null)
  );

  /* ================= DATA ================= */
  const title = product.name || "Combo";

  const price = Math.round(Number(product.selling_price || 0));

  const serves =
    product.serve_persons ||
    product.serves ||
    null;

  /* ================= EMOTIONAL LINE ================= */
  const getEmotionalLine = (product) => {
    if (Array.isArray(product.items)) {
      if (product.items.length >= 3) {
        return "Complete snack assortment for your cravings";
      }
      return "Traditional South Indian flavors, perfectly paired";
    }
    return "Fresh and authentic, made with care";
  };

  const getFoodIcon = (itemName) => {
    const name = (itemName || '').toLowerCase();
    if (name.includes('idli')) return '🫓';
    if (name.includes('dosa')) return '🥞';
    if (name.includes('sambar') || name.includes('rasam')) return '🍲';
    if (name.includes('chutney')) return '🥥';
    if (name.includes('murukku') || name.includes('mixture')) return '🍪';
    if (name.includes('sweet')) return '🍬';
    if (name.includes('coffee') || name.includes('tea')) return '☕';
    return '🍽️'; // Default food icon
  };

  /* ================= ADD ACTION ================= */
  const handleAdd = () => {
    addCombo(product, qty);
    openCheckout();
    onClose?.();
  };

  /* ================= EXPANDABLE INGREDIENTS ================= */
  const toggleExpanded = (itemIndex) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemIndex)) {
      newExpanded.delete(itemIndex);
    } else {
      newExpanded.add(itemIndex);
    }
    setExpandedItems(newExpanded);
  };

  const getIngredientIcon = (ingredientName) => {
    const name = (ingredientName || '').toLowerCase();
    if (name.includes('rice')) return '🌾';
    if (name.includes('urad') || name.includes('dal')) return '🫘';
    if (name.includes('wheat') || name.includes('flour')) return '🌾';
    if (name.includes('oil')) return '🫒';
    if (name.includes('salt')) return '🧂';
    if (name.includes('sugar')) return '🧁';
    if (name.includes('milk')) return '🥛';
    if (name.includes('coconut')) return '🥥';
    if (name.includes('chili') || name.includes('pepper')) return '🌶️';
    if (name.includes('onion')) return '🧅';
    if (name.includes('tomato')) return '🍅';
    if (name.includes('garlic')) return '🧄';
    if (name.includes('ginger')) return '🫚';
    if (name.includes('cumin') || name.includes('jeera')) return '🫚';
    if (name.includes('turmeric')) return '🫚';
    if (name.includes('coriander')) return '🌿';
    return '🥕'; // Default vegetable icon
  };

  /* ================= MOTION ================= */
  const modalAnim = reduceMotion
    ? {}
    : {
        hidden: { opacity: 0, y: 28 },
        visible: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: 20 },
      };

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center"
        onClick={onClose}
        variants={modalAnim}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <motion.div
          onClick={(e) => e.stopPropagation()}
          className="
            w-full max-w-2xl
            bg-card
            rounded-2xl
            overflow-hidden
            flex flex-col
            max-h-[95vh]
            shadow-2xl
          "
        >
          {/* ================= HERO IMAGE (4:3, EDGE-TO-EDGE) ================= */}
          <div className="relative aspect-[4/3] bg-black overflow-hidden">
            {image ? (
              <img
                src={image}
                alt={title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white/60 text-lg">
                Combo Image
              </div>
            )}

            {/* CLOSE BUTTON */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 bg-black/60 hover:bg-black/80 text-white rounded-full w-10 h-10 flex items-center justify-center transition-colors"
            >
              ✕
            </button>

            {/* FRESH TODAY BADGE */}
            <div className="absolute top-4 left-4 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
              Fresh today
            </div>
          </div>

          {/* ================= CONTENT ================= */}
          <div className="p-6 overflow-y-auto flex-1">
            {/* COMBO NAME (H1) */}
            <h1 className="text-2xl font-bold mb-2">{title}</h1>

            {/* EMOTIONAL LINE */}
            <p className="text-accent font-medium mb-6">
              {getEmotionalLine(product)}
            </p>

            {/* SERVES + FRESH TODAY (side by side) */}
            <div className="flex items-center justify-between mb-6">
              {serves && (
                <div className="flex items-center gap-2">
                  <span className="text-2xl">👥</span>
                  <div>
                    <div className="font-semibold">Serves {serves}</div>
                  </div>
                </div>
              )}
              <div className="flex items-center gap-2">
                <span className="text-green-500 text-xl">✓</span>
                <div>
                  <div className="font-semibold text-green-600">Fresh today</div>
                </div>
              </div>
            </div>

            {/* WHAT'S INSIDE - WITH INGREDIENT BREAKDOWN */}
            {isCombo && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">What's Inside</h3>
                <div className="space-y-3">
                  {product.items
                    .filter((item) => item.display_text)
                    .map((item, index) => {
                      const isExpanded = expandedItems.has(index);
                      const hasRecipe = item.recipe && item.recipe.length > 0;

                      return (
                        <div key={index} className="bg-surface rounded-lg overflow-hidden">
                          {/* ITEM HEADER - CLICKABLE */}
                          <button
                            onClick={() => hasRecipe && toggleExpanded(index)}
                            className={`w-full flex items-center gap-4 p-4 text-left hover:bg-white/5 transition-colors ${
                              hasRecipe ? 'cursor-pointer' : 'cursor-default'
                            }`}
                            disabled={!hasRecipe}
                          >
                            <div className="text-2xl">
                              {getFoodIcon(item.snack_name || item.display_text)}
                            </div>
                            <div className="flex-1">
                              <div className="font-medium">{item.display_text}</div>
                              {hasRecipe && (
                                <div className="text-sm text-muted mt-1">
                                  Tap to see ingredients
                                </div>
                              )}
                            </div>
                            {hasRecipe && (
                              <motion.div
                                animate={{ rotate: isExpanded ? 90 : 0 }}
                                transition={{ duration: 0.2 }}
                              >
                                <ChevronRight className="w-5 h-5 text-muted" />
                              </motion.div>
                            )}
                          </button>

                          {/* INGREDIENT BREAKDOWN - EXPANDABLE */}
                          <AnimatePresence>
                            {isExpanded && hasRecipe && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3, ease: "easeInOut" }}
                                className="border-t border-white/10"
                              >
                                <div className="p-4 bg-black/20">
                                  <div className="text-sm font-medium text-accent mb-3">
                                    Made with fresh ingredients:
                                  </div>
                                  <div className="grid grid-cols-1 gap-2">
                                    {item.recipe.map((recipeItem, recipeIndex) => (
                                      <motion.div
                                        key={recipeIndex}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: recipeIndex * 0.05 }}
                                        className="flex items-center gap-3 text-sm"
                                      >
                                        <div className="text-lg">
                                          {getIngredientIcon(recipeItem.ingredient_name)}
                                        </div>
                                        <div className="flex-1">
                                          <span className="font-medium">
                                            {recipeItem.ingredient_name}
                                          </span>
                                          <span className="text-muted ml-2">
                                            ({recipeItem.quantity} {recipeItem.quantity_unit})
                                          </span>
                                        </div>
                                      </motion.div>
                                    ))}
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}

            {/* PRICE - moved up for 5-second rule */}
            <div className="mb-6">
              <div className="text-3xl font-bold text-accent">₹{price}</div>
              <div className="text-sm text-muted">per combo</div>
            </div>
          </div>

          {/* ================= STICKY BOTTOM BAR ================= */}
          <div className="border-t border-subtle p-6 bg-card">
            <div className="flex items-center justify-center gap-4">
              {/* QUANTITY & ADD */}
              <div className="flex items-center gap-4">
                {/* QTY CONTROLS */}
                <div className="flex items-center gap-3 bg-surface rounded-lg p-1">
                  <button
                    onClick={() => setQty((q) => Math.max(1, q - 1))}
                    className="w-8 h-8 rounded-md hover:bg-white/10 flex items-center justify-center text-lg font-semibold"
                  >
                    −
                  </button>
                  <span className="w-8 text-center font-semibold">{qty}</span>
                  <button
                    onClick={() => setQty((q) => q + 1)}
                    className="w-8 h-8 rounded-md hover:bg-white/10 flex items-center justify-center text-lg font-semibold"
                  >
                    +
                  </button>
                </div>

                {/* STICKY REASSURANCE */}
                <div className="text-xs text-muted text-center max-w-32">
                  ✓ Exact quantity • ✓ Fresh today • ✓ No substitutions
                </div>

                {/* ADD BUTTON */}
                <button
                  onClick={handleAdd}
                  className="px-8 py-3 bg-accent text-black font-bold rounded-lg hover:bg-accent/90 transition-colors"
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
