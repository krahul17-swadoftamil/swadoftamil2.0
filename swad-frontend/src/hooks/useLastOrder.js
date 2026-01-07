import { useState, useEffect } from "react";

/* ======================================================
   useLastOrder — Smart Re-Order Hook
====================================================== */

const LAST_ORDER_KEY = "swad_last_order";

export function useLastOrder() {
  const [lastOrder, setLastOrder] = useState(null);

  // Load last order from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(LAST_ORDER_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Only show if ordered within last 7 days
        const orderDate = new Date(parsed.timestamp);
        const daysSince = (Date.now() - orderDate.getTime()) / (1000 * 60 * 60 * 24);

        if (daysSince <= 7) {
          setLastOrder(parsed);
        } else {
          // Clear old orders
          localStorage.removeItem(LAST_ORDER_KEY);
        }
      }
    } catch (error) {
      console.warn("Failed to load last order:", error);
    }
  }, []);

  // Save order to localStorage
  const saveLastOrder = (orderData) => {
    try {
      const data = {
        ...orderData,
        timestamp: new Date().toISOString(),
      };
      localStorage.setItem(LAST_ORDER_KEY, JSON.stringify(data));
      setLastOrder(data);
    } catch (error) {
      console.warn("Failed to save last order:", error);
    }
  };

  // Clear last order
  const clearLastOrder = () => {
    localStorage.removeItem(LAST_ORDER_KEY);
    setLastOrder(null);
  };

  return {
    lastOrder,
    saveLastOrder,
    clearLastOrder,
  };
}