import { useState } from "react";
import { api } from "../api";

/* ======================================================
   AccountModal — OTP Login / Signup
   Phone-first • Zero friction • ERP-aligned
====================================================== */

export default function AccountModal({ open, onClose, onSuccess }) {
  const [step, setStep] = useState("phone"); // phone | otp | profile
  const [loading, setLoading] = useState(false);

  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  if (!open) return null;

  /* ================= SEND OTP ================= */
  const sendOTP = async () => {
    if (!phone || phone.length < 10) return;

    setLoading(true);
    try {
      const res = await api.post("/auth/send-otp/", { phone });

      // If backend returns a plaintext OTP (development/testing),
      // prefill it so the tester doesn't have to type it.
      if (res?.otp) {
        setOtp(res.otp);
      }

      setStep("otp");
    } finally {
      setLoading(false);
    }
  };

  /* ================= VERIFY OTP ================= */
  const verifyOTP = async () => {
    // Accept short test OTPs (4 digits) as well as production 6-digit codes.
    if (!otp || otp.length < 4) return;

    setLoading(true);
    try {
      const res = await api.post("/auth/verify-otp/", {
        phone,
        // API expects `code` (see backend serializer). Send `code`.
        code: otp,
      });

      // Backend should return:
      // { customer, is_new_customer }
      if (res?.is_new_customer) {
        setStep("profile");
      } else {
        onSuccess?.(res.customer);
        onClose();
      }
    } finally {
      setLoading(false);
    }
  };

  /* ================= SAVE PROFILE (FIRST TIME) ================= */
  const saveProfile = async () => {
    setLoading(true);
    try {
      const res = await api.post("/auth/complete-profile/", {
        phone,
        name,
        email,
      });

      onSuccess?.(res.customer);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center">
      <div className="relative w-full max-w-md bg-card rounded-2xl p-6 shadow-xl">

        {/* CLOSE */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted"
        >
          ✕
        </button>

        {/* ======================================================
            STEP 1 — PHONE
        ====================================================== */}
        {step === "phone" && (
          <>
            <h2 className="text-lg font-semibold mb-2">
              Enter your mobile number
            </h2>
            <p className="text-sm text-muted mb-4">
              We’ll send a one-time password to verify you.
            </p>

            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="10-digit mobile number"
              className="input w-full"
            />

            <button
              onClick={sendOTP}
              disabled={loading}
              className="btn-primary w-full mt-4"
            >
              {loading ? "Sending OTP…" : "Send OTP"}
            </button>
          </>
        )}

        {/* ======================================================
            STEP 2 — OTP
        ====================================================== */}
        {step === "otp" && (
          <>
            <h2 className="text-lg font-semibold mb-2">
              Verify OTP
            </h2>
            <p className="text-sm text-muted mb-4">
              Enter the 6-digit code sent to {phone}
            </p>

            <input
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="6-digit OTP"
              className="input w-full tracking-widest text-center"
            />

            <button
              onClick={verifyOTP}
              disabled={loading}
              className="btn-primary w-full mt-4"
            >
              {loading ? "Verifying…" : "Verify"}
            </button>

            <button
              onClick={() => setStep("phone")}
              className="mt-3 text-xs text-muted underline"
            >
              Change phone number
            </button>
          </>
        )}

        {/* ======================================================
            STEP 3 — FIRST TIME PROFILE
        ====================================================== */}
        {step === "profile" && (
          <>
            <h2 className="text-lg font-semibold mb-2">
              Welcome 👋
            </h2>
            <p className="text-sm text-muted mb-4">
              Just one last step before ordering.
            </p>

            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              className="input w-full mb-3"
            />

            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email (optional)"
              className="input w-full"
            />

            <button
              onClick={saveProfile}
              disabled={loading}
              className="btn-primary w-full mt-4"
            >
              {loading ? "Saving…" : "Continue"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
