import { useEffect, useState } from "react";
import { useCart } from "../context/CartContext";
import CheckoutModal from "./CheckoutModal";

export default function FloatingCart() {
  const {
    cart,
    itemCount,
    total,
    incItem,
    decItem,
    removeItem,
    incCombo,
    decCombo,
    removeCombo,
    incSnack,
    decSnack,
    removeSnack,
  } = useCart();

  const [openCheckout, setOpenCheckout] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (itemCount > 0) setVisible(true);
  }, [itemCount]);

  if (!visible) return null;

  const { combos = [], items = [], snacks = [] } = cart;

  return (
    <>
      <div className="fixed bottom-6 right-6 z-50 w-80 bg-card rounded-2xl shadow-xl border border-subtle">
        <div className="p-4 font-semibold">
          Your Cart ({itemCount})
        </div>

        <div className="max-h-64 overflow-y-auto px-4 space-y-3">
          {[...combos, ...items, ...snacks].map((x) => (
            <div key={x.id} className="flex justify-between items-center">
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">
                  {x.name}
                </div>
                <div className="text-xs text-muted">
                  ₹{x.price} × {x.qty}
                </div>
              </div>

              <div className="flex gap-2">
                <button onClick={() => decItem(x.id)}>−</button>
                <button onClick={() => incItem(x.id)}>+</button>
                <button onClick={() => removeItem(x.id)}>✕</button>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-subtle">
          <div className="flex justify-between font-bold mb-3">
            <span>Total</span>
            <span>₹{total}</span>
          </div>

          <button
            onClick={() => setOpenCheckout(true)}
            className="w-full py-3 rounded-xl bg-accent text-black font-semibold"
          >
            Proceed to Checkout →
          </button>
        </div>
      </div>

      {/* CHECKOUT */}
      {openCheckout && (
        <CheckoutModal onClose={() => setOpenCheckout(false)} />
      )}
    </>
  );
}
