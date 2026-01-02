import { useState, useCallback } from "react";
import { useCart } from "../context/CartContext";

import QuickCheckoutModal from "./QuickCheckoutModal";
import SuccessModal from "./SuccessModal";

/* ======================================================
   CheckoutContainer — Global Checkout Orchestrator
====================================================== */

export default function CheckoutContainer() {
  const {
    checkoutOpen,
    closeCheckout,
    placeOrderAsync,
    isPlacingOrder,
  } = useCart();

  const [successOpen, setSuccessOpen] = useState(false);
  const [placedOrder, setPlacedOrder] = useState(null);

  /* ================= PLACE ORDER ================= */

  const handlePlace = useCallback(
    async (customer) => {
      if (isPlacingOrder) return;

      try {
        const res = await placeOrderAsync(customer);

        closeCheckout();

        if (res) {
          setPlacedOrder(res);
          setSuccessOpen(true);
        }

        return res;
      } catch (err) {
        alert(err?.message || "Failed to place order");
        throw err;
      }
    },
    [placeOrderAsync, closeCheckout, isPlacingOrder]
  );

  /* ================= UI ================= */

  return (
    <>
      {/* CHECKOUT MODAL */}
      <QuickCheckoutModal
        open={checkoutOpen}
        onClose={closeCheckout}
        onPlace={handlePlace}
        placing={isPlacingOrder}
      />

      {/* SUCCESS MODAL */}
      <SuccessModal
        open={successOpen}
        order={placedOrder}
        onClose={() => {
          setSuccessOpen(false);
          setPlacedOrder(null);
        }}
      />
    </>
  );
}
