import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import GoogleSignInButton from "../components/GoogleSignInButton";

/* ======================================================
   MobileSignup — Clean & Correct
   • Phone OTP OR Google
   • No redirects
   • Session-based auth
====================================================== */

export default function MobileSignup() {
  const {
    sendOTP,
    login,
    completeProfile,
    user,
    isAuthenticated,
  } = useAuth();

  const navigate = useNavigate();

  // Get post-login redirect from sessionStorage
  const postLoginRedirect = sessionStorage.getItem('postLoginRedirect');

  const [step, setStep] = useState("phone"); // phone | otp | profile | success
  const [loading, setLoading] = useState(false);

  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const isDev = Boolean(import.meta.env.DEV);

  /* ================= REDIRECT IF LOGGED IN ================= */
  useEffect(() => {
    if (isAuthenticated && user) {
      navigate("/");
    }
  }, [isAuthenticated, user, navigate]);

  /* ================= SEND OTP ================= */
  const handleSendOTP = async () => {
    if (phone.length !== 10) {
      setError("Enter a valid 10-digit number");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const res = await sendOTP(phone);

      if (isDev && res.otp) {
        setMessage(`Dev OTP: ${res.otp}`);
      } else {
        setMessage("OTP sent to your number");
      }

      setStep("otp");
    } catch {
      setError("Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  /* ================= VERIFY OTP ================= */
  const handleVerifyOTP = async () => {
    if (otp.length !== 4) {
      setError("Enter 4-digit OTP");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const res = await login(phone, otp);
      const isNew = res.is_new_customer || res.isNew;

      if (isNew) {
        setStep("profile");
      } else {
        setStep("success");
        setTimeout(() => navigate("/"), 1500);
      }
    } catch {
      setError("Invalid OTP");
      setOtp("");
    } finally {
      setLoading(false);
    }
  };

  /* ================= SAVE PROFILE ================= */
  const handleSaveProfile = async () => {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await completeProfile(name.trim(), email.trim() || null);
      setStep("success");
      setTimeout(() => navigate("/"), 1500);
    } catch {
      setError("Failed to save profile");
    } finally {
      setLoading(false);
    }
  };

  /* ================= UI ================= */
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md space-y-6">

        {/* LOGO */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-accent">Swad</h1>
          <p className="text-sm text-muted">Tamil Food Delivery</p>
        </div>

        {/* CARD */}
        <div className="bg-card p-6 rounded-3xl border border-subtle space-y-6">

          {/* STEP: PHONE */}
          {step === "phone" && (
            <>
              <div>
                <h2 className="text-xl font-bold">Get Started</h2>
                <p className="text-sm text-muted">
                  Verify with OTP or continue with Google
                </p>
              </div>

              <input
                value={phone}
                onChange={(e) =>
                  setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))
                }
                placeholder="10-digit mobile number"
                inputMode="numeric"
                className="w-full px-4 py-3 rounded-xl bg-surface border"
              />

              {error && <p className="text-sm text-red-400">{error}</p>}
              {message && <p className="text-sm text-green-400">{message}</p>}

              {/* GOOGLE */}
              <GoogleSignInButton postLoginRedirect={postLoginRedirect} />

              <div className="text-center text-xs text-muted">OR</div>

              <button
                onClick={handleSendOTP}
                disabled={loading || phone.length !== 10}
                className="w-full py-3 rounded-xl bg-accent text-black font-semibold disabled:opacity-50"
              >
                Send OTP
              </button>

              {isDev && (
                <div className="text-xs text-blue-400 text-center">
                  Dev OTP: <b>1234</b>
                </div>
              )}
            </>
          )}

          {/* STEP: OTP */}
          {step === "otp" && (
            <>
              <h2 className="text-xl font-bold">Verify OTP</h2>

              <input
                value={otp}
                onChange={(e) =>
                  setOtp(e.target.value.replace(/\D/g, "").slice(0, 4))
                }
                placeholder="••••"
                inputMode="numeric"
                className="w-full px-4 py-3 text-center text-2xl rounded-xl bg-surface border"
              />

              {error && <p className="text-sm text-red-400">{error}</p>}

              <button
                onClick={handleVerifyOTP}
                disabled={loading || otp.length !== 4}
                className="w-full py-3 rounded-xl bg-accent text-black font-semibold"
              >
                Verify OTP
              </button>

              <button
                onClick={() => setStep("phone")}
                className="w-full py-2 text-sm text-muted"
              >
                Change number
              </button>
            </>
          )}

          {/* STEP: PROFILE */}
          {step === "profile" && (
            <>
              <h2 className="text-xl font-bold">Complete Profile</h2>

              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                className="w-full px-4 py-3 rounded-xl bg-surface border"
              />

              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email (optional)"
                type="email"
                className="w-full px-4 py-3 rounded-xl bg-surface border"
              />

              {error && <p className="text-sm text-red-400">{error}</p>}

              <button
                onClick={handleSaveProfile}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-accent text-black font-semibold"
              >
                Continue
              </button>
            </>
          )}

          {/* STEP: SUCCESS */}
          {step === "success" && (
            <div className="text-center space-y-2">
              <div className="text-4xl">✅</div>
              <p className="font-semibold">Welcome!</p>
              <p className="text-sm text-muted">Redirecting…</p>
            </div>
          )}
        </div>

        {/* FOOTER */}
        <p className="text-xs text-muted text-center">
          By continuing, you agree to our Terms & Privacy Policy
        </p>
      </div>
    </div>
  );
}
