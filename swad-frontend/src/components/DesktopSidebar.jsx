import { useMemo } from "react";
import { motion } from "framer-motion";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";

/* ======================================================
   DesktopSidebar — Premium Cart + Trust Column
====================================================== */

export default function DesktopSidebar({ marketingOffers = [] }) {
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
  const todaysOffer = marketingOffers.find(
    (o) => o.is_active && o.banner_type === "limited_time"
  );

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
    <aside className="hidden lg:block w-80 xl:w-96 sticky top-10 h-fit space-y-6">
      {/* ================= CART ================= */}
      <motion.div
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-card/50 backdrop-blur-sm border border-subtle/50 rounded-2xl p-4"
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold text-text">Your Cart</h3>
          <span className="text-xs text-muted">{itemCount} items</span>
        </div>

        {/* Empty */}
        {cartItems.length === 0 && (
          <div className="py-6 text-center text-muted">
            <div className="text-3xl mb-2">🛒</div>
            <p className="text-sm">Your Tamil breakfast awaits</p>
          </div>
        )}

        {/* Items */}
        {cartItems.length > 0 && (
          <div className="space-y-3 mb-4">
            {cartItems.slice(0, 4).map((item) => (
              <div
                key={`${item.type}-${item.id}`}
                className="flex items-center gap-3"
              >
                {/* Qty Control */}
                <div className="flex items-center border border-subtle rounded-lg overflow-hidden">
                  <button
                    onClick={() => dec(item)}
                    className="px-2 py-1 text-sm hover:bg-white/5"
                  >
                    −
                  </button>
                  <span className="px-2 text-sm font-medium">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => inc(item)}
                    className="px-2 py-1 text-sm hover:bg-white/5"
                  >
                    +
                  </button>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 flex items-center gap-3">
                  <img
                    src={resolveMediaUrl(item.image || item.primary_image)}
                    alt={item.name}
                    className="w-10 h-10 rounded-lg object-cover flex-shrink-0"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjRjNGNEY2Ii8+Cjx0ZXh0IHg9IjIwIiB5PSIyNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzk5OSI+8J+RjzwvdGV4dD4KPHN2Zz4=';
                    }}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">
                      {item.name}
                    </p>
                    <p className="text-xs text-muted">
                      ₹{item.price}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {cartItems.length > 4 && (
              <p className="text-xs text-muted">
                +{cartItems.length - 4} more items
              </p>
            )}
          </div>
        )}

        {/* Total */}
        {itemCount > 0 && (
          <>
            <div className="flex justify-between items-center pt-3 border-t border-subtle">
              <span className="text-sm text-muted">Total</span>
              <span className="text-lg font-bold text-accent">
                ₹{total}
              </span>
            </div>

            <button
              onClick={openCheckout}
              className="mt-3 w-full bg-accent text-black font-semibold py-2.5 rounded-xl hover:bg-accent/90 transition"
            >
              View Cart & Checkout
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
          className="bg-card/50 backdrop-blur-sm border border-subtle/50 rounded-2xl p-4"
        >
          <h4 className="font-semibold text-text mb-1">
            🎯 Today’s Special
          </h4>
          <p className="text-sm text-muted">
            {todaysOffer.title}
          </p>
          {todaysOffer.description && (
            <p className="text-xs text-muted mt-1">
              {todaysOffer.description}
            </p>
          )}
        </motion.div>
      )}

      {/* ================= DELIVERY PROMISE ================= */}
      <motion.div
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-card/50 backdrop-blur-sm border border-subtle/50 rounded-2xl p-4"
      >
        <h4 className="font-semibold text-text mb-3">
          🚚 Fresh Delivery Promise
        </h4>

        <ul className="space-y-2 text-sm text-muted">
          <li>• Prepared fresh every morning</li>
          <li>• Delivered hot within 30 mins,Porter Partner</li>
          <li>• Authentic Tamil recipes</li>
        </ul>

        <div className="mt-3 text-xs font-medium text-text bg-card/30 rounded-lg p-2 text-center">
          Order before 10 AM to 11 AM for same-day delivery
        </div>
      </motion.div>
    </aside>
  );
}
