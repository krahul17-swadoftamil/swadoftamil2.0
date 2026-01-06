import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ======================================================
   OTPModal — Instant Checkout Verification
   • Dev mode support (test OTP: 1234)
   • Production SMS-based OTP
   • Auto-submit on 4 digits in dev
====================================================== */

export default function OTPModal({ onConfirm, onCancel }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const isDev = Boolean(import.meta?.env?.DEV);
  const TEST_OTP = "1234";

  /* ================= KEYBOARD ================= */
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onCancel?.();
      // Auto-submit on 4 digits in dev mode
      if (isDev && e.key === "Enter" && code.length === 4) handleConfirm();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [code, isDev, onCancel]);

  /* ================= CONFIRM ================= */
  async function handleConfirm() {
    if (submitting) return;

    setError(null);

    if (code.length !== 4) {
      setError("Enter 4-digit OTP");
      return;
    }

    try {
      setSubmitting(true);

      // In dev mode, validate against test OTP
      if (isDev && code !== TEST_OTP) {
        throw new Error("Invalid OTP (dev mode)");
      }

      // Delegate verification / continuation to parent
      await onConfirm(code);

    } catch (err) {
      setError(err?.message || "OTP verification failed");
      setSubmitting(false);
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-50 flex items-end md:items-center justify-center"
      >
        {/* BACKDROP */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50"
          onClick={!submitting ? onCancel : undefined}
        />

        {/* MODAL */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ 
            duration: 0.3, 
            ease: "easeOut",
            scale: { type: "spring", damping: 25, stiffness: 300 }
          }}
          className="relative w-full max-w-md bg-card rounded-t-2xl md:rounded-2xl p-6"
        >
        <h3 className="text-lg font-semibold mb-1">
          Verify your order
        </h3>

        <p className="text-sm text-muted mb-3">
          Enter the 4-digit OTP sent to your number to confirm checkout.
        </p>

        {isDev && (
          <div className="mb-3 text-xs text-blue-400 bg-blue-400/10 p-2 rounded">
            Dev mode · Test OTP: <b>1234</b> · Press Enter to confirm
          </div>
        )}

        {/* OTP INPUT */}
        <input
          value={code}
          onChange={(e) =>
            setCode(
              e.target.value.replace(/\D/g, "").slice(0, 4)
            )
          }
          inputMode="numeric"
          autoFocus
          placeholder="••••"
          className="
            w-full p-3 mb-2
            rounded-lg
            text-center text-xl tracking-widest
            bg-surface
            focus:outline-none focus:ring-2 focus:ring-accent
            disabled:opacity-50
          "
          disabled={submitting}
        />

        {/* ERROR */}
        {error && (
          <div className="text-sm text-red-400 mb-2">
            {error}
          </div>
        )}

        {/* ACTIONS */}
        <div className="flex items-center gap-3">
          <button
            onClick={onCancel}
            disabled={submitting}
            className="px-4 py-2 rounded-full bg-surface text-muted disabled:opacity-50"
          >
            Cancel
          </button>

          <button
            onClick={handleConfirm}
            disabled={code.length !== 4 || submitting}
            className="
              ml-auto px-5 py-2 rounded-full
              bg-accent text-white font-semibold
              disabled:opacity-50
            "
          >
            {submitting ? "Verifying…" : "Confirm"}
          </button>
        </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
