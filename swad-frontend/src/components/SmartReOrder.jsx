import { useState } from "react";
import { motion } from "framer-motion";
import { useCart } from "../context/CartContext";
import { useLastOrder } from "../hooks/useLastOrder";

/* ======================================================
   SmartReOrder — 1-Tap Re-Order Feature
====================================================== */

function SmartReOrder({ onReOrder }) {
  const { lastOrder } = useLastOrder();
  const { addCombo, addItem, addSnack, openCheckout } = useCart();
  const [isReordering, setIsReordering] = useState(false);

  if (!lastOrder) return null;

  // Get the main item from the last order
  const getMainItem = () => {
    if (lastOrder.combos?.length > 0) {
      return { type: "combo", ...lastOrder.combos[0] };
    }
    if (lastOrder.items?.length > 0) {
      return { type: "item", ...lastOrder.items[0] };
    }
    if (lastOrder.snacks?.length > 0) {
      return { type: "snack", ...lastOrder.snacks[0] };
    }
    return null;
  };

  const mainItem = getMainItem();
  if (!mainItem) return null;

  const handleReOrder = async () => {
    setIsReordering(true);

    try {
      // Add the main item to cart
      if (mainItem.type === "combo") {
        addCombo(mainItem, mainItem.quantity || 1);
      } else if (mainItem.type === "item") {
        addItem(mainItem, mainItem.quantity || 1);
      } else if (mainItem.type === "snack") {
        addSnack(mainItem, mainItem.quantity || 1);
      }

      // Add any additional items from the order
      if (lastOrder.combos?.length > 1) {
        lastOrder.combos.slice(1).forEach(combo => addCombo(combo, combo.quantity || 1));
      }
      if (lastOrder.items?.length > 1) {
        lastOrder.items.slice(1).forEach(item => addItem(item, item.quantity || 1));
      }
      if (lastOrder.snacks?.length > 1) {
        lastOrder.snacks.slice(1).forEach(snack => addSnack(snack, snack.quantity || 1));
      }

      // Open checkout
      setTimeout(() => {
        openCheckout();
        onReOrder?.();
      }, 500);

    } catch (error) {
      console.error("Re-order failed:", error);
    } finally {
      setIsReordering(false);
    }
  };

  const itemName = mainItem.name || "Breakfast Item";
  const itemPrice = mainItem.price || mainItem.unit_price || 0;
  const quantity = mainItem.quantity || 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="bg-gradient-to-r from-accent/10 to-accent/5 border border-accent/20 rounded-2xl p-6 mx-4"
    >
      <div className="text-center space-y-4">
        {/* Header */}
        <div className="flex items-center justify-center gap-2">
          <span className="text-2xl">🔁</span>
          <h3 className="text-lg font-bold text-accent">
            Order Yesterday's Breakfast
          </h3>
        </div>

        {/* Item Details */}
        <div className="space-y-2">
          <p className="text-lg font-semibold">
            {itemName}
            {quantity > 1 && ` (×${quantity})`}
          </p>
          <p className="text-xl font-bold text-accent">
            ₹{itemPrice * quantity}
          </p>
        </div>

        {/* Re-Order Button */}
        <motion.button
          onClick={handleReOrder}
          disabled={isReordering}
          className="w-full bg-accent text-black font-bold py-3 px-6 rounded-xl hover:bg-accent/90 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          whileTap={{ scale: 0.98 }}
        >
          {isReordering ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
              Adding to Cart...
            </span>
          ) : (
            "🔁 Re-Order Now"
          )}
        </motion.button>

        {/* Subtle hint */}
        <p className="text-xs text-muted">
          70% of customers re-order the same breakfast
        </p>
      </div>
    </motion.div>
  );
}

export default SmartReOrder;