import { useState, useEffect } from "react";

/* ======================================================
   useOrderCount — Soft Loyalty Tracking
====================================================== */

const ORDER_COUNT_KEY = "swad_order_count";

export function useOrderCount() {
  const [orderCount, setOrderCount] = useState(0);

  // Load order count from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(ORDER_COUNT_KEY);
      if (stored) {
        const count = parseInt(stored, 10);
        if (!isNaN(count) && count >= 0) {
          setOrderCount(count);
        }
      }
    } catch (error) {
      console.warn("Failed to load order count:", error);
    }
  }, []);

  // Increment order count
  const incrementOrderCount = () => {
    try {
      const newCount = orderCount + 1;
      setOrderCount(newCount);
      localStorage.setItem(ORDER_COUNT_KEY, newCount.toString());
    } catch (error) {
      console.warn("Failed to save order count:", error);
    }
  };

  // Reset order count (for testing/debugging)
  const resetOrderCount = () => {
    setOrderCount(0);
    localStorage.removeItem(ORDER_COUNT_KEY);
  };

  return {
    orderCount,
    incrementOrderCount,
    resetOrderCount,
  };
}