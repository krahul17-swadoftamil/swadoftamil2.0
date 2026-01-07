import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import { ChevronLeft, ChevronRight } from "lucide-react";

/* ======================================================
   DesktopSidebar — Minimal Cart + Optional Offers
====================================================== */

export default function DesktopSidebar({ marketingOffers = [] }) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  
  const {
    cart,
    itemCount,
    total,
    openCheckout,
    incCombo,
    decCombo,
    incItem,
    decItem,
    incSnack,
    decSnack,
  } = useCart();

  /* ================= TODAY'S OFFER ================= */
  const todaysOffer = useMemo(() => {
    // Only show the highest priority active offer
    const activeOffers = marketingOffers.filter(o => o.is_active);
    if (activeOffers.length === 0) return null;
    
    // Sort by priority (higher number = higher priority) and take the first
    return activeOffers.sort((a, b) => (b.priority || 0) - (a.priority || 0))[0];
  }, [marketingOffers]);

  /* ================= NORMALIZE CART ================= */
  const cartItems = useMemo(() => {
    return [
      ...(cart.combos || []).map((c) => ({ ...c, type: "combo" })),
      ...(cart.items || []).map((i) => ({ ...i, type: "item" })),
      ...(cart.snacks || []).map((s) => ({ ...s, type: "snack" })),
    ];
  }, [cart]);

  /* ================= QTY HANDLER ================= */
  const inc = (item) => {
    if (item.type === "combo") incCombo(item.id);
    if (item.type === "item") incItem(item.id);
    if (item.type === "snack") incSnack(item.id);
  };

  const dec = (item) => {
    if (item.type === "combo") decCombo(item.id);
    if (item.type === "item") decItem(item.id);
    if (item.type === "snack") decSnack(item.id);
  };

  return (
    <div className="hidden lg:block sticky top-10">
      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="mb-4 p-2 bg-surface/30 backdrop-blur-sm border border-subtle/30 rounded-lg hover:bg-surface/50 transition-colors"
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-text" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-text" />
        )}
      </button>

      {/* Sidebar Content */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.aside
            initial={{ opacity: 0, x: 24, width: 0 }}
            animate={{ opacity: 1, x: 0, width: 288 }}
            exit={{ opacity: 0, x: 24, width: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="w-72 space-y-4 overflow-hidden"
          >
            {/* ================= CART ================= */}
            <motion.div
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-surface/30 backdrop-blur-sm border border-subtle/30 rounded-xl p-3"
            >
              {/* Header */}
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-medium text-text text-sm">Your Cart</h3>
                <span className="text-xs text-muted">{itemCount} items</span>
              </div>

              {/* Empty */}
              {cartItems.length === 0 && (
                <div className="py-4 text-center text-muted">
                  <div className="text-2xl mb-1">🛒</div>
                  <p className="text-xs">Your Tamil breakfast awaits</p>
                </div>
              )}

              {/* Items */}
              {cartItems.length > 0 && (
                <div className="space-y-2 mb-3">
                  {cartItems.slice(0, 3).map((item) => (
                    <div
                      key={`${item.type}-${item.id}`}
                      className="flex items-center gap-2"
                    >
                      {/* Qty Control */}
                      <div className="flex items-center border border-subtle/50 rounded-md overflow-hidden">
                        <button
                          onClick={() => dec(item)}
                          className="px-1.5 py-0.5 text-xs hover:bg-white/5"
                        >
                          −
                        </button>
                        <span className="px-1.5 text-xs font-medium">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => inc(item)}
                          className="px-1.5 py-0.5 text-xs hover:bg-white/5"
                        >
                          +
                        </button>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0 flex items-center gap-2">
                        <img
                          src={resolveMediaUrl(item.image || item.primary_image)}
                          alt={item.name}
                          className="w-8 h-8 rounded object-cover flex-shrink-0"
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjRjNGNEY2Ii8+Cjx0ZXh0IHg9IjE2IiB5PSIyMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzk5OSI+8J+RjzwvdGV4dD4KPHN2Zz4=';
                          }}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium truncate">
                            {item.name}
                          </p>
                          <p className="text-xs text-muted">
                            ₹{item.price}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {cartItems.length > 3 && (
                    <p className="text-xs text-muted">
                      +{cartItems.length - 3} more items
                    </p>
                  )}
                </div>
              )}

              {/* Total */}
              {itemCount > 0 && (
                <>
                  <div className="flex justify-between items-center pt-2 border-t border-subtle/30">
                    <span className="text-xs text-muted">Total</span>
                    <span className="text-sm font-bold text-accent">
                      ₹{total}
                    </span>
                  </div>

                  <button
                    onClick={openCheckout}
                    className="mt-2 w-full bg-accent text-black font-medium py-2 rounded-lg hover:bg-accent/90 transition text-sm"
                  >
                    View Cart
                  </button>
                </>
              )}
            </motion.div>

            {/* ================= TODAY'S OFFER ================= */}
            {todaysOffer && (
              <motion.div
                initial={{ opacity: 0, x: 24 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.05 }}
                className="bg-surface/20 backdrop-blur-sm border border-subtle/20 rounded-xl p-3"
              >
                <h4 className="font-medium text-text text-sm mb-1">
                  🎯 {todaysOffer.banner_type === 'limited_time' ? 'Limited Time' : 'Special Offer'}
                </h4>
                <p className="text-xs text-muted">
                  {todaysOffer.short_text || todaysOffer.title}
                </p>
              </motion.div>
            )}

            {/* ================= DELIVERY PROMISE ================= */}
            <motion.div
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-surface/20 backdrop-blur-sm border border-subtle/20 rounded-xl p-3"
            >
              <h4 className="font-medium text-text text-sm mb-2">
                🚚 Fresh Delivery
              </h4>

              <div className="text-xs text-muted space-y-1">
                <div>• Made fresh daily</div>
                <div>• Hot delivery in 30 mins</div>
                <div>• Authentic Tamil recipes</div>
              </div>
            </motion.div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
