import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useOrderCount } from "../hooks/useOrderCount";

/* ======================================================
   LoyaltyIndicator — Soft Loyalty (No Coins, No Noise)
====================================================== */

function LoyaltyIndicator() {
  const { orderCount } = useOrderCount();
  const [show, setShow] = useState(false);

  // Only show if user has ordered at least once
  useEffect(() => {
    if (orderCount > 0) {
      // Small delay for better UX
      const timer = setTimeout(() => setShow(true), 1000);
      return () => clearTimeout(timer);
    }
  }, [orderCount]);

  if (!show || orderCount === 0) return null;

  // Get appropriate message based on order count
  const getMessage = (count) => {
    if (count === 1) {
      return "Welcome back! Thank you for choosing Swad of Tamil";
    } else if (count < 5) {
      return `You've had Swad of Tamil ${count} times. Thank you for trusting us`;
    } else {
      return `🫶 You've had Swad of Tamil ${count} times. Thank you for trusting us`;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="text-center py-2"
    >
      <p className="text-sm text-muted font-medium leading-relaxed">
        {getMessage(orderCount)}
      </p>
    </motion.div>
  );
}

export default LoyaltyIndicator;