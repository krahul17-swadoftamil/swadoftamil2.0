import { useState } from "react";

export default function OTPModal({ onConfirm, onCancel }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);

  // Vite provides import.meta.env.DEV when running in development
  const isDev = Boolean(import.meta.env && import.meta.env.DEV);
  const TEST_OTP = isDev ? "1234" : null;

  const handleConfirm = () => {
    setError(null);
    if (isDev) {
      if (code !== TEST_OTP) {
        setError("Invalid OTP");
        return;
      }
      // In dev, short-circuit and report the test OTP
      onConfirm(code);
      return;
    }

    onConfirm(code);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onCancel} />
      <div className="relative w-full max-w-md bg-card rounded-t-2xl md:rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-2">Verify your order</h3>
        <p className="text-sm text-muted mb-2">Enter the 4-digit OTP sent to your number to confirm the instant checkout.</p>

        {isDev && (
          <div className="mb-3 text-xs text-muted">Use test OTP: 1234</div>
        )}

        <div className="flex gap-2 mb-2">
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/[^0-9]/g, "").slice(0,4))}
            className="w-full p-3 rounded-lg text-center text-xl tracking-widest bg-surface"
            inputMode="numeric"
            placeholder="----"
          />
        </div>

        {error && <div className="text-sm text-red-400 mb-2">{error}</div>}

        <div className="flex items-center gap-3">
          <button onClick={onCancel} className="px-4 py-2 rounded-full bg-surface text-muted">Cancel</button>
          <button
            onClick={handleConfirm}
            disabled={code.length !== 4}
            className="ml-auto px-4 py-2 rounded-full bg-accent text-white font-semibold disabled:opacity-50"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
