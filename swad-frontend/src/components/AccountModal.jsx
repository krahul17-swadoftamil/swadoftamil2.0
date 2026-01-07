import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import GoogleSignInButton from "./GoogleSignInButton";

/* ======================================================
   AccountModal — FIXED
   • Controlled by `open`
   • Auto-unmounts on success
   • No zombie overlays
====================================================== */

export default function AccountModal({ open, onClose, onSuccess }) {
  const { sendOTP, login, completeProfile, firebaseLogin } = useAuth();

  const [step, setStep] = useState("phone");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  /* ================= RESET ON OPEN ================= */
  useEffect(() => {
    if (open) {
      setStep("phone");
      setLoading(false);
      setError(null);
      setPhone("");
      setOtp("");
      setName("");
      setEmail("");
      setRememberMe(false);
    }
  }, [open]);

  /* 🚨 HARD STOP — THIS WAS MISSING */
  // if (!open) return null; // Commented out for AnimatePresence

  /* ================= SEND OTP ================= */
  const sendOtpHandler = async () => {
    if (phone.length !== 10) {
      setError("Enter valid 10-digit number");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await sendOTP(phone);
      if (res?.otp) setOtp(res.otp);
      setStep("otp");
    } catch (e) {
      setError(e?.message || "OTP failed");
    } finally {
      setLoading(false);
    }
  };

  /* ================= VERIFY OTP ================= */
  const verifyOtpHandler = async () => {
    if (otp.length !== 4) {
      setError("Enter 4-digit OTP");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await login(phone, otp);
      const isNew = res.isNew || res.is_new_customer;

      if (isNew) {
        setStep("profile");
      } else {
        onSuccess?.(res.customer);
        onClose(); // ✅ CLOSE IMMEDIATELY
      }
    } catch (e) {
      setError("Invalid OTP");
      setOtp("");
    } finally {
      setLoading(false);
    }
  };

  /* ================= SAVE PROFILE ================= */
  const saveProfileHandler = async () => {
    if (!name.trim()) {
      setError("Name required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await completeProfile(phone, name.trim(), email.trim() || null);
      onSuccess?.(res.customer);
      onClose(); // ✅ CLOSE IMMEDIATELY
    } catch (e) {
      setError("Profile save failed");
    } finally {
      setLoading(false);
    }
  };

  /* ================= GOOGLE ================= */
  const googleHandler = async (cred) => {
    setLoading(true);
    setError(null);
    try {
      const res = await googleLogin(cred);
      onSuccess?.(res.customer);
      onClose(); // ✅ CLOSE
    } catch {
      setError("Google login failed");
    } finally {
      setLoading(false);
    }
  };

  /* ======================================================
     RENDER
  ====================================================== */
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 bg-black/60 flex items-end md:items-center justify-center"
          onClick={onClose}
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
            className="relative w-full max-w-md bg-card rounded-t-2xl md:rounded-2xl p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
        {/* CLOSE */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted hover:text-foreground"
        >
          ✕
        </button>

        <>
        {/* ================= PHONE ================= */}
        {step === "phone" && (
          <>
            <h2 className="text-2xl font-bold mb-2 font-heading">Get Started</h2>
            <p className="text-sm text-muted mb-6">
              Sign in with Google or verify your mobile number
            </p>

            <GoogleSignInButton
              className="w-full mb-4"
              rememberMe={rememberMe}
            />

            <div className="flex items-center mb-4">
              <input
                type="checkbox"
                id="rememberMe"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="rememberMe" className="text-sm text-muted">
                Remember me for 30 days
              </label>
            </div>

            <div className="relative mb-4">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted">Or</span>
              </div>
            </div>

            <input
              value={phone}
              onChange={(e) =>
                setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))
              }
              className="w-full px-4 py-3 rounded-xl bg-surface border"
              placeholder="10-digit number"
              autoFocus
            />

            {error && <p className="text-red-400 mt-3">{error}</p>}

            <button
              onClick={sendOtpHandler}
              disabled={loading || phone.length !== 10}
              className="mt-4 w-full py-3 rounded-xl bg-accent text-black font-semibold"
            >
              Send OTP
            </button>
          </>
        )}

        {/* ================= OTP ================= */}
        {step === "otp" && (
          <>
            <h2 className="text-2xl font-bold mb-2 font-heading">Verify OTP</h2>
            <input
              value={otp}
              onChange={(e) =>
                setOtp(e.target.value.replace(/\D/g, "").slice(0, 4))
              }
              className="w-full px-4 py-3 rounded-xl bg-surface border text-center text-2xl tracking-widest"
              autoFocus
            />

            {error && <p className="text-red-400 mt-3">{error}</p>}

            <button
              onClick={verifyOtpHandler}
              disabled={loading || otp.length !== 4}
              className="mt-4 w-full py-3 rounded-xl bg-accent text-black font-semibold"
            >
              Verify
            </button>
          </>
        )}

        {/* ================= PROFILE ================= */}
        {step === "profile" && (
          <>
            <h2 className="text-2xl font-bold mb-2 font-heading">Welcome 👋</h2>

            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-surface border mb-3"
              placeholder="Full Name"
              autoFocus
            />

            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-surface border"
              placeholder="Email (optional)"
            />

            {error && <p className="text-red-400 mt-3">{error}</p>}

            <button
              onClick={saveProfileHandler}
              disabled={loading || !name.trim()}
              className="mt-4 w-full py-3 rounded-xl bg-accent text-black font-semibold"
            >
              Continue
            </button>
          </>
        )}
        </>
        </motion.div>
      </motion.div>
    )}
    </AnimatePresence>
  );
}
