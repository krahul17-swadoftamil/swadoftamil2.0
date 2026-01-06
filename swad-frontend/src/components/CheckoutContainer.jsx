import { useState, useCallback, useRef } from "react";
import { useCart } from "../context/CartContext";

import QuickCheckoutModal from "./QuickCheckoutModal";
import SuccessModal from "./SuccessModal";

/* ======================================================
   CheckoutContainer — CLEAN ORCHESTRATOR
   • Single checkout flow
   • Centralized state
   • ERP-aligned
   • Prevents duplicate orders
====================================================== */

export default function CheckoutContainer() {
  const {
    checkoutOpen,
    closeCheckout,
    placeOrderAsync,
  } = useCart();

  const [createdOrder, setCreatedOrder] = useState(null);

  const [successOpen, setSuccessOpen] = useState(false);
  const [order, setOrder] = useState(null);
  
  // ✔ Prevent duplicate orders with ref
  const orderInFlightRef = useRef(false);

  /* ================= PLACE ORDER ================= */
  const handlePlace = useCallback(
    async (customerPayload) => {
      // ✔ Double-submit guard at container level
      if (orderInFlightRef.current) {
        throw new Error("Order submission already in progress");
      }

      orderInFlightRef.current = true;

      try {
        // placeOrderAsync:
        // ✔ throws on failure
        // ✔ returns created order on success
        // ✔ clears cart on success
        const createdOrder = await placeOrderAsync(customerPayload);

        // Store the created order for success display
        setCreatedOrder(createdOrder);

        // Don't close checkout here - let QuickCheckoutModal handle success feedback
        // closeCheckout();

        // Skip success modal - handled by QuickCheckoutModal
        // setOrder(createdOrder);
        // setSuccessOpen(true);

        return createdOrder;
      } finally {
        orderInFlightRef.current = false;
      }
    },
    [placeOrderAsync, closeCheckout]
  );

  /* ================= RENDER ================= */
  return (
    <>
      {/* ================= CHECKOUT ================= */}
      <QuickCheckoutModal
        open={checkoutOpen}
        onClose={closeCheckout}
        onPlace={handlePlace}
        createdOrder={createdOrder}
      />

      {/* ================= SUCCESS ================= */}
      <SuccessModal
        open={successOpen}
        order={order}
        onClose={() => {
          setSuccessOpen(false);
          setOrder(null);
        }}
      />
    </>
  );
}
