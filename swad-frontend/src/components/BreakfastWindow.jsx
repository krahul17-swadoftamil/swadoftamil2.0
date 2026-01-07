import { useState, useEffect } from "react";
import { api } from "../api";

/* ======================================================
   BreakfastWindow — Django-Driven Status Card
   Premium UI with night mode support
====================================================== */

export default function BreakfastWindow() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get("/system/breakfast-window/");
        setStatus(response.data);
        setError(null);
      } catch (err) {
        console.warn("Failed to fetch breakfast window status:", err);
        setError("Unable to check breakfast status");
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    // Update every minute for live status
    const timer = setInterval(fetchStatus, 60000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-6 text-center shadow-sm">
        <div className="animate-pulse">
          <div className="h-6 bg-amber-200 rounded mb-2"></div>
          <div className="h-4 bg-amber-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-200 rounded-xl p-6 text-center shadow-sm">
        <div className="text-gray-600">
          <span className="text-2xl">🕒</span>
          <div className="mt-2 text-sm">Breakfast Status</div>
          <div className="text-xs text-muted mt-1">Check back later</div>
        </div>
      </div>
    );
  }

  const { is_open, status_label, status_message } = status;

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-6 text-center shadow-sm">
      <div className="flex items-center justify-center gap-2 mb-3">
        <span className="text-2xl">🕒</span>
        <span className="font-bold text-lg text-foreground">Today's Breakfast Window</span>
      </div>

      <div className="space-y-2">
        <div className={`text-xl font-bold ${is_open ? 'text-green-700' : 'text-red-600'}`}>
          {is_open ? '🟢 Now Open' : '🔴 Now Closed'}
        </div>

        <div className="text-sm text-foreground font-medium">
          {status_message}
        </div>

        {/* Status label for additional context */}
        <div className="text-xs text-muted uppercase tracking-wide">
          {status_label}
        </div>
      </div>
    </div>
  );
}