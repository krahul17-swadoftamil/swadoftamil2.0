import { useState } from "react";
import { useCart } from "../context/CartContext";
import { placeOrder } from "../api";

export default function CheckoutModal({ onClose }) {
  const [step, setStep] = useState("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [paymentSession, setPaymentSession] = useState(null);
  const [orderData, setOrderData] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState("online");

  const { cart, total, clearCart } = useCart();

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center">
      <div className="bg-card w-full max-w-md rounded-2xl p-6">

        {step === "phone" && (
          <>
            <h2 className="text-lg font-semibold mb-4">
              Enter your phone number
            </h2>
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="10-digit mobile number"
              className="input"
            />
            <button
              onClick={() => setStep("otp")}
              className="btn-primary w-full mt-4"
            >
              Send OTP
            </button>
          </>
        )}

        {step === "otp" && (
          <>
            <h2 className="text-lg font-semibold mb-4">
              Verify OTP
            </h2>
            <input
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="Enter OTP"
              className="input"
            />
            <button
              onClick={() => setStep("address")}
              className="btn-primary w-full mt-4"
            >
              Verify
            </button>
          </>
        )}

        {step === "address" && (
          <>
            <h2 className="text-lg font-semibold mb-4">
              Delivery Address
            </h2>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="input"
              placeholder="House, Street, Area"
            />
            <button
              onClick={() => setStep("payment")}
              className="btn-primary w-full mt-4"
            >
              Continue
            </button>
          </>
        )}

        {step === "payment" && (
          <>
            <h2 className="text-lg font-semibold mb-4">
              Payment
            </h2>
            <div className="mb-4">
              <div className="text-sm text-muted">Amount</div>
              <div className="text-lg font-semibold">₹{total}</div>
            </div>
            <div className="mb-4">
              <div className="text-sm text-muted">Payment method</div>
              <div className="flex gap-3 mt-2">
                <label className="flex items-center gap-2">
                  <input type="radio" name="pm" value="online" checked={paymentMethod==="online"} onChange={()=>setPaymentMethod("online")}/>
                  <span>Pay Online</span>
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" name="pm" value="cod" checked={paymentMethod==="cod"} onChange={()=>setPaymentMethod("cod")}/>
                  <span>Cash on Delivery</span>
                </label>
              </div>
            </div>
            <button
              onClick={async () => {
                if (loading) return;
                setLoading(true);

                const payload = {
                  combos: (cart.combos || []).map((c) => ({ id: c.id, quantity: c.qty })),
                  items: (cart.items || []).map((i) => ({ item_id: i.id, quantity: i.qty })),
                  snacks: (cart.snacks || []).map((s) => ({ snack_id: s.id, quantity: s.qty })),
                  customer: {
                    name,
                    phone,
                    email: "",
                    address,
                  },
                  payment_method: paymentMethod,
                };

                try {
                  const res = await placeOrder(payload);
                  // backend returns { order, payment_session }
                  setOrderData(res.order || null);
                  setPaymentSession(res.payment_session || null);
                  setStep("payment-sim");
                } catch (err) {
                  console.error(err);
                  alert(err.message || "Failed to initiate checkout");
                } finally {
                  setLoading(false);
                }
              }}
              className="btn-primary w-full"
            >
              {loading ? "Processing…" : "Pay Now"}
            </button>
          </>
        )}

        {step === "payment-sim" && (
          <>
            <h2 className="text-lg font-semibold mb-4">Simulate Payment</h2>
            <div className="mb-4 text-sm text-muted">Session: {paymentSession?.slice(0,8)}...</div>
            <button
              className="btn-primary w-full mb-2"
              onClick={async () => {
                // simulate successful payment
                try {
                  setLoading(true);
                  await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/orders/checkout_confirm/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ order_id: orderData?.id, payment_session: paymentSession })
                  });

                  // clear cart and close
                  clearCart();
                  setStep('success');
                } catch (err) {
                  console.error(err);
                  alert('Payment confirm failed');
                } finally {
                  setLoading(false);
                }
              }}
            >
              Simulate Success
            </button>
            <button className="btn-muted w-full" onClick={() => setStep('payment')}>
              Back
            </button>
          </>
        )}

        {step === 'success' && (
          <>
            <h2 className="text-lg font-semibold mb-4">Order Placed</h2>
            <p className="mb-4">Thank you — your order is confirmed.</p>
            <button className="btn-primary w-full" onClick={() => { onClose(); window.location.href = '/' }}>
              Back to Home
            </button>
          </>
        )}

        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-muted"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
