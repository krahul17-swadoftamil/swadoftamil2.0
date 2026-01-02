import { useEffect, useState } from "react";
import { useCart } from "../context/CartContext";

/* ======================================================
   QuickCheckoutModal — FINAL (Clean & Safe)
====================================================== */

export default function QuickCheckoutModal({ open, onClose, onPlace }) {
  const {
    cart,
    total,
    itemCount,

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

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [errors, setErrors] = useState({});

  /* ================= ESC CLOSE ================= */
  useEffect(() => {
    if (!open) return;
    const esc = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);

  if (!open) return null;

  const combos = cart.combos || [];
  const items = cart.items || [];
  const snacks = cart.snacks || [];
  const empty = itemCount === 0;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full sm:max-w-lg bg-card rounded-t-3xl sm:rounded-2xl max-h-[92vh] flex flex-col"
      >
        {/* ================= HEADER ================= */}
        <div className="p-4 border-b border-subtle flex justify-between items-start">
          <div>
            <h2 className="text-lg font-semibold">Confirm order</h2>
            <p className="text-xs text-muted">Fresh morning batch</p>
          </div>

          <button
            onClick={onClose}
            className="h-8 w-8 flex items-center justify-center rounded-full border border-subtle"
          >
            ✕
          </button>
        </div>

        {/* ================= ITEMS ================= */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {empty && (
            <div className="text-center text-sm text-muted py-10">
              Cart is empty
            </div>
          )}

          {combos.map((c) => (
            <Row
              key={`combo-${c.id}`}
              name={c.name}
              qty={c.qty}
              onInc={() => incCombo(c.id)}
              onDec={() => decCombo(c.id)}
              onRemove={() => removeCombo(c.id)}
            />
          ))}

          {items.map((i) => (
            <Row
              key={`item-${i.id}`}
              name={i.name}
              qty={i.qty}
              onInc={() => incItem(i.id)}
              onDec={() => decItem(i.id)}
              onRemove={() => removeItem(i.id)}
            />
          ))}

          {snacks.map((s) => (
            <Row
              key={`snack-${s.id}`}
              name={s.name}
              qty={s.qty}
              onInc={() => incSnack(s.id)}
              onDec={() => decSnack(s.id)}
              onRemove={() => removeSnack(s.id)}
            />
          ))}
        </div>

        {/* ================= FOOTER ================= */}
        <div className="border-t border-subtle p-4 space-y-3">
          <div className="space-y-3">
            <div className="flex justify-between text-lg font-bold">
              <span>Total</span>
              <span className="text-accent">₹{total}</span>
            </div>

              <div className="space-y-2">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Name (optional)"
                  className="w-full input"
                />

                <div>
                  <input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Phone (required)"
                    onBlur={() => {
                      // basic validation on blur
                      const v = (phone || "").trim();
                      const eobj = {};
                      if (!v) eobj.phone = "Phone is required";
                      else if (!/^\+?\d{7,15}$/.test(v)) eobj.phone = "Enter a valid phone number";
                      setErrors((s) => ({ ...s, ...eobj }));
                    }}
                    className={`w-full input ${errors.phone ? "border-red-400" : ""}`}
                  />
                  {errors.phone && <div className="text-red-500 text-xs mt-1">{errors.phone}</div>}
                </div>

                <div>
                  <input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email (optional)"
                    onBlur={() => {
                      if (!email) return setErrors((s) => ({ ...s, email: undefined }));
                      const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
                      setErrors((s) => ({ ...s, email: ok ? undefined : "Enter a valid email" }));
                    }}
                    className={`w-full input ${errors.email ? "border-red-400" : ""}`}
                  />
                  {errors.email && <div className="text-red-500 text-xs mt-1">{errors.email}</div>}
                </div>

                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Address (optional)"
                  className="w-full input"
                />
              </div>

              <button
                disabled={empty || !!errors.phone || !!errors.email || !phone}
                onClick={() => {
                  // final validation
                  const errs = {};
                  const v = (phone || "").trim();
                  if (!v) errs.phone = "Phone is required";
                  else if (!/^\+?\d{7,15}$/.test(v)) errs.phone = "Enter a valid phone number";
                  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = "Enter a valid email";
                  setErrors(errs);
                  if (Object.keys(errs).length) return;
                  onPlace && onPlace({ name, phone: v, email: (email || "").trim(), address });
                }}
                className="w-full py-3 rounded-2xl bg-accent text-black font-semibold disabled:opacity-50"
              >
                Place Order
              </button>
          </div>

          <p className="text-xs text-muted text-center">
            Exact prepared quantities · No conversion
          </p>
        </div>
      </div>
    </div>
  );
}

/* ======================================================
   Row — Single Line Item
====================================================== */

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
        <button
          onClick={onRemove}
          className="text-muted hover:text-red-400 ml-1"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
