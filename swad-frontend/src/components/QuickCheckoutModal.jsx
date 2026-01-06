import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";

/* ======================================================
   QuickCheckoutModal — FAST COD EDITION
   • 1-tap checkout
   • Memory-assisted
   • ERP-safe
====================================================== */

const PHONE_KEY = "swad_last_phone";

export default function QuickCheckoutModal({ open, onClose, onPlace, createdOrder }) {
  const navigate = useNavigate();
  const { isAuthenticated, setPostLoginRedirectUrl } = useAuth();
  const {
    cart,
    total,
    itemCount,
    incItem, decItem, removeItem,
    incCombo, decCombo, removeCombo,
    incSnack, decSnack, removeSnack,
    clearCart,
    freeDeliveryProgress,
    suggestedAddons,
    lastAddedItem,
    clearAnimation,
  } = useCart();

  /* ================= CUSTOMER ================= */
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cod"); // Default to COD

  /* ================= STATE ================= */
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [orderData, setOrderData] = useState(null);

  /* ================= PREFILL ================= */
  useEffect(() => {
    if (!open) return;
    const saved = localStorage.getItem(PHONE_KEY);
    if (saved) setPhone(saved);
  }, [open]);

  /* ================= SYNC CREATED ORDER ================= */
  useEffect(() => {
    setOrderData(createdOrder);
  }, [createdOrder]);

  /* ================= ITEM ADDED ANIMATION ================= */
  useEffect(() => {
    if (lastAddedItem) {
      // Clear animation after 2 seconds
      const timer = setTimeout(() => {
        clearAnimation();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [lastAddedItem, clearAnimation]);

  /* ================= ESC ================= */
  useEffect(() => {
    if (!open) return;
    const esc = (e) => e.key === "Escape" && !processing && !success && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, processing, success, onClose]);

  if (!open) return null;

  const combos = cart.combos || [];
  const items = cart.items || [];
  const snacks = cart.snacks || [];
  const empty = itemCount === 0;

  /* ================= VALIDATION ================= */
  function validate() {
    const v = phone.trim();
    if (!v) return "Phone number is required";
    if (!/^\+?\d{7,15}$/.test(v)) return "Enter a valid phone number";
    return null;
  }

  /* ================= PLACE ORDER ================= */
  async function handlePlace() {
    // Allow guest checkout for all orders (no login required)
    
    // ✔ Double-submit guard
    if (processing) return;

    const err = validate();
    if (err) {
      setError(err);
      return;
    }

    try {
      setProcessing(true);
      setError(null);

      localStorage.setItem(PHONE_KEY, phone.trim());

      // Handle online payment
      if (paymentMethod === "online") {
        // For now, show payment gateway placeholder
        alert("💳 Online Payment Gateway Coming Soon!\n\nPlease select Cash on Delivery for now.");
        setProcessing(false);
        return;
      }

      // ✔ COD: Let onPlace handle the actual order + success flow
      const result = await onPlace({
        phone: phone.trim(),
        name: name.trim() || null,
        address: address.trim() || null,
        payment_method: paymentMethod,
      });

      // Show success state
      setProcessing(false);
      setSuccess(true);

      // Auto-close after success animation (moved to useEffect)
      // setTimeout(() => {
      //   onClose?.();
      //   setSuccess(false);
      // }, 2000);

      return result;

    } catch (e) {
      // ✔ Show error but don't auto-close (allows retry)
      setError(e?.message || "Could not place order");
      setProcessing(false);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center"
          onClick={!processing && !success ? onClose : undefined}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ 
              duration: 0.3, 
              ease: "easeOut",
              scale: { type: "spring", damping: 25, stiffness: 300 }
            }}
            onClick={(e) => e.stopPropagation()}
            className="w-full sm:max-w-lg bg-card rounded-t-3xl sm:rounded-2xl max-h-[92vh] flex flex-col"
          >
        {/* ITEM ADDED NOTIFICATION */}
        {lastAddedItem && (
          <div className="bg-green-500 text-white px-4 py-2 text-sm font-medium text-center animate-in slide-in-from-top-2 duration-300">
            ✅ Added {lastAddedItem.name} to cart!
          </div>
        )}

        {/* ================= HEADER ================= */}
        <div className="p-4 border-b border-subtle">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-lg font-semibold">Fast Checkout</h2>
              <p className="text-xs text-muted">
                <span className={`inline-block px-2 py-0.5 rounded-full mr-1 ${
                  paymentMethod === "cod"
                    ? "bg-green-500/10 text-green-400"
                    : "bg-blue-500/10 text-blue-400"
                }`}>
                  {paymentMethod === "cod" ? "💵 COD" : "💳 Online"}
                </span>
                {paymentMethod === "cod"
                  ? "Pay on delivery · Ready in 30–45 mins"
                  : "Secure online payment · Instant confirmation"
                }
              </p>
            </div>

            <button
              disabled={processing}
              onClick={onClose}
              className="h-8 w-8 rounded-full border border-subtle disabled:opacity-40"
            >
              ✕
            </button>
          </div>
        </div>

        {/* ================= ITEMS ================= */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {empty && (
            <div className="text-center text-sm text-muted py-10">
              Your Tamil breakfast awaits
            </div>
          )}

          {combos.map((c) => (
            <Row key={`c-${c.id}`} {...rowProps(c, incCombo, decCombo, removeCombo)} />
          ))}
          {items.map((i) => (
            <Row key={`i-${i.id}`} {...rowProps(i, incItem, decItem, removeItem)} />
          ))}
          {snacks.map((s) => (
            <Row key={`s-${s.id}`} {...rowProps(s, incSnack, decSnack, removeSnack)} />
          ))}
        </div>

        {/* ================= STICKY FOOTER ================= */}
        <div className="border-t border-subtle p-4 space-y-3">
          <div className={`flex justify-between text-lg font-bold transition-all duration-300 ${
            lastAddedItem ? 'scale-105 text-green-600' : ''
          }`}>
            <span>Total</span>
            <span className="text-accent">₹{total}</span>
          </div>

          {/* FREE DELIVERY PROGRESS */}
          {freeDeliveryProgress && (
            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/30 rounded-lg p-3">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-amber-600">🚚</span>
                <span className="text-amber-800 dark:text-amber-200 font-medium">
                  Add ₹{freeDeliveryProgress} more for FREE delivery!
                </span>
              </div>
            </div>
          )}

          {/* SUGGESTED ADD-ONS */}
          {suggestedAddons.length > 0 && (
            <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800/30 rounded-lg p-3">
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <span className="font-medium">✨ Suggested:</span>
                <div className="mt-1 space-y-1">
                  {suggestedAddons.map((addon, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span>{addon.name} - {addon.reason}</span>
                      <span className="font-medium">₹{addon.price}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* PAYMENT METHOD SELECTION */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Payment Method</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPaymentMethod("cod")}
                disabled={processing}
                className="p-3 rounded-lg border-2 border-accent bg-accent/10 text-accent font-semibold disabled:opacity-50"
              >
                💵 Cash on Delivery
              </button>
              <button
                type="button"
                onClick={() => setPaymentMethod("online")}
                disabled={processing}
                className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                  paymentMethod === "online"
                    ? "border-accent bg-accent/5 text-accent"
                    : "border-subtle text-muted hover:border-accent/50"
                } disabled:opacity-50`}
              >
                💳 Online Payment
              </button>
            </div>
          </div>

          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value.replace(/[^0-9+]/g, ""))}
            placeholder="Phone number"
            inputMode="numeric"
            autoFocus
            disabled={processing}
            className={`w-full input ${error ? "border-red-400" : ""}`}
          />

          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name (optional)"
            disabled={processing}
            className="w-full input"
          />

          <input
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Address (optional)"
            disabled={processing}
            className="w-full input"
          />

          {error && (
            <div className="text-red-500 text-sm text-center">{error}</div>
          )}

          {success && orderData ? (
            <div className="space-y-4">
              {/* Order Details */}
              <div className="text-center space-y-3">
                <div className="text-4xl">✅</div>
                <div className="text-xl font-bold text-green-600">Order Placed Successfully</div>
                <div className="space-y-1">
                  <div className="text-sm text-muted">
                    Order #{orderData.order_number}
                  </div>
                  <div className="text-sm text-muted">
                    Ready in {orderData.eta_minutes} minutes
                  </div>
                  <div className="text-sm text-muted">
                    Payment: {orderData.payment_method === "cod" ? "Cash on Delivery" : "Online Payment"}
                  </div>
                </div>
              </div>

              {/* ENGAGEMENT CALLS-TO-ACTION */}
              <div className="space-y-3 pt-2">
                <div className="grid grid-cols-1 gap-2">
                  <button className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800/70 transition-colors text-left">
                    <span className="text-lg">⭐</span>
                    <span className="text-sm font-medium">Rate your experience later</span>
                  </button>
                  
                  <button className="flex items-center gap-3 p-3 bg-pink-50 dark:bg-pink-900/20 rounded-lg hover:bg-pink-100 dark:hover:bg-pink-900/30 transition-colors text-left">
                    <span className="text-lg">📸</span>
                    <span className="text-sm font-medium">Tag us on Instagram @swadoftamil</span>
                  </button>
                  
                  <button className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors text-left">
                    <span className="text-lg">🔁</span>
                    <span className="text-sm font-medium">Reorder in 1 tap</span>
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-1 gap-3">
                <button
                  type="button"
                  onClick={() => {
                    navigate(`/order/${orderData.id}`);
                    onClose?.();
                    setSuccess(false);
                    setOrderData(null);
                  }}
                  className="py-3 rounded-2xl font-semibold bg-accent text-black hover:bg-accent/90 transition-colors"
                >
                  Track Order
                </button>
                <button
                  type="button"
                  onClick={() => {
                    navigate("/");
                    onClose?.();
                    setSuccess(false);
                    setOrderData(null);
                  }}
                  className="py-3 rounded-2xl font-semibold bg-gray-100 text-gray-800 hover:bg-gray-200 transition-colors"
                >
                  Back to Home
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              disabled={empty || processing}
              onClick={success ? () => {
                onClose?.();
                setSuccess(false);
              } : handlePlace}
              className={`w-full py-4 rounded-2xl font-semibold disabled:opacity-50 transition-all duration-200 ${
                success
                  ? "bg-green-500 text-white"
                  : "bg-accent text-black"
              }`}
            >
              {processing ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
                  <span>Placing order…</span>
                </div>
              ) : success ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center">
                    <span className="text-sm">✓</span>
                  </div>
                  <span>Order Confirmed!</span>
                </div>
              ) : paymentMethod === "cod" ? (
                <div className="text-center">
                  <div className="text-lg font-bold">Confirm Order · ₹{total}</div>
                  <div className="text-sm opacity-90">Pay on Delivery</div>
                </div>
              ) : (
                "Proceed to Payment"
              )}
            </button>
          )}

          <p className="text-xs text-muted text-center">
            No login · No advance payment · Confirmed instantly
          </p>
        </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ================= HELPERS ================= */

function rowProps(x, inc, dec, remove) {
  return {
    name: x.name,
    qty: x.qty,
    onInc: () => inc(x.id),
    onDec: () => dec(x.id),
    onRemove: () => remove(x.id),
  };
}

function Row({ name, qty, onInc, onDec, onRemove }) {
  return (
    <div className="flex justify-between items-center gap-3">
      <div className="min-w-0">
        <div className="text-sm font-medium truncate">{name}</div>
        <div className="text-xs text-muted">Qty: {qty}</div>
      </div>

      <div className="flex items-center gap-2">
        <button onClick={onDec} className="qty-pill">−</button>
        <span className="font-semibold w-5 text-center">{qty}</span>
        <button onClick={onInc} className="qty-pill">+</button>
        <button onClick={onRemove} className="text-muted hover:text-red-400">
          ✕
        </button>
      </div>
    </div>
  );
}
