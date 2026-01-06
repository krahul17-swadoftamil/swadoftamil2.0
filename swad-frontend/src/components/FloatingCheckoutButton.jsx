import { motion, AnimatePresence } from "framer-motion";
import { useCart } from "../context/CartContext";

/* ======================================================
   FloatingCheckoutButton — Global Checkout Trigger
   Single source of truth: CartContext
====================================================== */

export default function FloatingCheckoutButton() {
  const {
    itemCount,
    total,
    openCheckout, // ✅ GLOBAL CHECKOUT CONTROL
  } = useCart();

  const visible = itemCount > 0 && total > 0;

  return (
    <AnimatePresence>
      {visible && (
        <motion.button
          key="floating-checkout"
          onClick={openCheckout}
          initial={{ opacity: 0, y: 24 }}
          animate={{ 
            opacity: 1, 
            y: 0,
            scale: [1, 1.05, 1],
          }}
          exit={{ opacity: 0, y: 24 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={{ 
            duration: 0.25, 
            ease: "easeOut",
            scale: {
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }
          }}
          className="
            fixed bottom-6 right-6 z-40
            flex items-center gap-3
            px-4 py-3
            rounded-full
            bg-accent text-black
            font-semibold
            shadow-[0_12px_40px_rgba(0,0,0,0.35)]
            focus:outline-none
            focus:ring-2 focus:ring-accent/60
          "
          aria-label="View cart and checkout"
        >
          {/* ITEM COUNT */}
          <span
            className="
              h-8 w-8 rounded-full
              bg-black/15
              flex items-center justify-center
              text-sm font-bold
            "
          >
            {itemCount}
          </span>

          {/* TOTAL */}
          <span className="text-sm font-semibold">
            ₹{total}
          </span>

          {/* CTA */}
          <span className="text-xs opacity-80 whitespace-nowrap">
            View order
          </span>
        </motion.button>
      )}
    </AnimatePresence>
  );
}
