import { motion, AnimatePresence } from "framer-motion";
import { useCart } from "../context/CartContext";

/* ======================================================
   FloatingCheckoutButton — Global Cart CTA
====================================================== */

export default function FloatingCheckoutButton() {
  const { itemCount, total, openCheckout } = useCart();

  if (!itemCount) return null;

  return (
    <AnimatePresence>
      <motion.button
        onClick={openCheckout}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.96 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="
          fixed bottom-6 right-6 z-40
          flex items-center gap-3
          px-4 py-3
          rounded-full
          bg-accent text-black
          font-semibold
          shadow-xl
        "
        aria-label="View cart and checkout"
      >
        {/* COUNT */}
        <span className="h-8 w-8 rounded-full bg-black/10 flex items-center justify-center text-sm font-bold">
          {itemCount}
        </span>

        {/* TOTAL */}
        <span className="text-sm">
          ₹{total}
        </span>

        {/* CTA */}
        <span className="text-xs opacity-80">
          View order
        </span>
      </motion.button>
    </AnimatePresence>
  );
}
