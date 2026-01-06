import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

export default function SuccessModal({ open, order, onClose }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return;
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);

  if (!open) return null; // Keep for now, will remove for AnimatePresence

  const id = order?.id || null;
  const orderNumber = order?.order_number || id;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-60 bg-black/50 flex items-center justify-center"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ 
              duration: 0.4, 
              ease: "easeOut",
              scale: { type: "spring", damping: 20, stiffness: 200 }
            }}
            onClick={(e) => e.stopPropagation()}
            className="bg-card p-6 rounded-2xl max-w-sm w-full text-center"
          >
        <div className="text-4xl mb-2">✅</div>
        <h2 className="text-lg font-semibold">Order placed</h2>
        <p className="text-sm text-muted mt-2">Thank you — your order is received.</p>

        {orderNumber && (
          <div className="mt-3 font-mono text-sm bg-surface p-2 rounded">{orderNumber}</div>
        )}

        <div className="mt-4 flex gap-2">
          <button
            onClick={() => {
              onClose?.();
              navigate("/");
            }}
            className="flex-1 py-2 rounded-lg border border-subtle"
          >
            Back to home
          </button>

          {id && (
            <button
              onClick={() => {
                onClose?.();
                navigate(`/order/${id}`);
              }}
              className="flex-1 py-2 rounded-lg bg-accent text-black font-semibold"
            >
              View order
            </button>
          )}
        </div>
        </motion.div>
      </motion.div>
    )}
    </AnimatePresence>
  );
}
