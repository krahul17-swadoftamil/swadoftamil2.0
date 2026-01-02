import { useEffect, useMemo, useState } from "react";
import {
  motion,
  AnimatePresence,
  useReducedMotion,
} from "framer-motion";

import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";

/* ================= Helpers ================= */
function formatQty(qty, unit) {
  if (!qty || !unit) return "";
  return `${Math.round(qty)} ${unit}`;
}

/* ================= AI RANKING ================= */
function rankAddons(product, addons) {
  if (!Array.isArray(addons) || !product) return [];

  const comboNames =
    product.items?.map((i) =>
      String(i.prepared_item_name || "").toLowerCase()
    ) || [];

  return addons
    .map((a) => {
      let score = 0;
      const name = String(a.name || "").toLowerCase();

      if (comboNames.includes("idli") && name.includes("vada")) score += 3;
      if (name.includes("protein")) score += 2;
      if (name.includes("chutney") || name.includes("podi")) score += 2;
      if (a.morning_only) score += 2;
      if (Number(a.selling_price) <= 40) score += 1;
      if (a.is_best_buy) score += 2;

      return { ...a, _score: score };
    })
    .sort((a, b) => b._score - a._score)
    .slice(0, 3);
}

/* ======================================================
   ProductDetailModal — DISCIPLINED COMMERCE (v4.1)
====================================================== */

export default function ProductDetailModal({
  product,
  addons = [],
  onClose,
  onOpenItems,
  onOpenSnacks,
}) {
  const {
    addCombo,
    addItem,
    addSnack,
    openCheckout,
  } = useCart();

  const [qty, setQty] = useState(1);
  const reduceMotion = useReducedMotion();

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
      product.image_url ||
      (Array.isArray(product.images)
        ? product.images[0]
        : null)
  );

  /* ================= DATA ================= */
  const title = product.name || "Product";
  const description =
    product.long_description ||
    product.description ||
    "Prepared fresh every morning using authentic Tamil methods.";

  const price = Math.round(Number(product.selling_price || 0));
  const mrp = product.mrp ? Math.round(product.mrp) : null;
  const serves =
    product.serves || (isCombo ? "2–3 people" : "1 person");
  const maxQty = Number(product.max_possible_quantity || 5);

  /* ================= SMART ADDONS ================= */
  const smartAddons = useMemo(
    () => rankAddons(product, addons),
    [product, addons]
  );

  /* ================= ACTION ================= */
  const handleAdd = () => {
    if (isCombo) {
      addCombo(product, qty);
    } else {
      addItem(product, qty);
    }
    openCheckout();
    onClose?.();
  };

  /* ================= MOTION ================= */
  const modalAnim = {
    hidden: { opacity: 0, y: reduceMotion ? 0 : 24 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 16 },
  };

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center"
        onClick={onClose}
        variants={modalAnim}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <motion.div
          onClick={(e) => e.stopPropagation()}
          className="w-full sm:max-w-lg bg-card rounded-t-3xl sm:rounded-2xl overflow-hidden flex flex-col"
        >
          {/* IMAGE */}
          <motion.div
            className="h-56 bg-surface flex items-center justify-center"
            initial={reduceMotion ? false : { scale: 0.96 }}
            animate={reduceMotion ? false : { scale: 1 }}
          >
            {image && (
              <img
                src={image}
                alt={title}
                className="max-h-full object-contain p-4"
              />
            )}
          </motion.div>

          {/* CONTENT */}
          <div className="p-5 space-y-4 flex-1 overflow-y-auto">
            <div className="flex justify-between items-start">
              <h2 className="text-xl font-bold">{title}</h2>
              <button onClick={onClose}>✕</button>
            </div>

            <p className="text-sm text-muted">{description}</p>

            {/* WHY */}
            <div className="bg-surface rounded-xl p-4 text-sm">
              <div className="font-semibold mb-1">Why this?</div>
              <ul className="list-disc pl-4 text-muted space-y-1">
                <li>Single-batch morning preparation</li>
                <li>Traditional fermentation & slow cooking</li>
                <li>Balanced, light, digestion-friendly</li>
              </ul>
            </div>

            {/* INCLUDED */}
            {isCombo && (
              <div className="text-sm space-y-1">
                <div className="font-semibold">What’s included</div>
                {product.items.map((i, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between text-muted"
                  >
                    <span>{i.prepared_item_name}</span>
                    <span>
                      {formatQty(i.display_quantity, i.unit)}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* SMART ADDONS */}
            {smartAddons.length > 0 && (
              <div className="space-y-2">
                <div className="font-semibold text-sm">
                  Best with this combo 🧠
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {smartAddons.map((a) => (
                    <motion.button
                      key={a.id}
                      whileHover={reduceMotion ? {} : { y: -2 }}
                      onClick={() =>
                        a.type === "snack"
                          ? addSnack(a, 1)
                          : addItem(a, 1)
                      }
                      className="flex gap-3 items-center bg-surface rounded-xl p-2"
                    >
                      <img
                        src={resolveMediaUrl(a.image)}
                        alt={a.name}
                        className="h-12 w-12 rounded-lg object-cover"
                      />
                      <div className="text-left text-xs">
                        <div className="font-medium">{a.name}</div>
                        <div className="text-muted">
                          ₹{Math.round(a.selling_price)}
                          {a.mrp && (
                            <span className="line-through ml-1 opacity-50">
                              ₹{Math.round(a.mrp)}
                            </span>
                          )}
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {isCombo && (
              <div className="flex justify-between text-xs pt-2">
                <button onClick={onOpenItems} className="underline">
                  View items
                </button>
                <button
                  onClick={onOpenSnacks}
                  className="text-accent font-semibold"
                >
                  Browse snacks
                </button>
              </div>
            )}
          </div>

          {/* FOOTER */}
          <div className="border-t border-subtle p-4 space-y-3">
            <div className="flex justify-between">
              <div>
                <div className="text-xs text-muted">Price</div>
                <div className="text-2xl font-bold text-accent">
                  ₹{price}
                </div>
                {mrp && (
                  <div className="text-xs line-through text-muted">
                    MRP ₹{mrp}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() =>
                    setQty((q) => Math.max(1, q - 1))
                  }
                >
                  −
                </button>
                <span>{qty}</span>
                <button
                  onClick={() =>
                    setQty((q) => Math.min(maxQty, q + 1))
                  }
                >
                  +
                </button>
              </div>
            </div>

            <button
              className="btn-primary w-full"
              onClick={handleAdd}
            >
              Add to order
            </button>

            <p className="text-xs text-muted text-center">
              Exact quantities · Limited batches · Fast checkout
            </p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
