import { useEffect, useState } from "react";
import { useParams, useNavigate, Navigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircleIcon,
  ClockIcon,
  TruckIcon,
  ChefHatIcon,
  MapPinIcon,
} from "lucide-react";

import { api } from "../api";
import { useAuth } from "../context/AuthContext";

/* ======================================================
   CONSTANTS & HELPERS
====================================================== */

const STATUS_FLOW = [
  { key: "placed", label: "Order Placed", icon: CheckCircleIcon, bg: "bg-blue-500" },
  { key: "confirmed", label: "Confirmed", icon: ChefHatIcon, bg: "bg-orange-500" },
  { key: "preparing", label: "Preparing", icon: ChefHatIcon, bg: "bg-yellow-500" },
  { key: "out_for_delivery", label: "Out for Delivery", icon: TruckIcon, bg: "bg-purple-500" },
  { key: "delivered", label: "Delivered", icon: MapPinIcon, bg: "bg-green-500" },
];

const EVENT_LABELS = {
  placed: "Order Placed",
  confirmed: "Order Confirmed",
  preparing: "Started Preparing",
  out_for_delivery: "Out for Delivery",
  delivered: "Delivered",
  cancelled: "Order Cancelled",
};

const getStatusIndex = (status) =>
  STATUS_FLOW.findIndex((s) => s.key === status);

const getProgressPercent = (status) => {
  const i = getStatusIndex(status);
  return i === -1 ? 0 : ((i + 1) / STATUS_FLOW.length) * 100;
};

/* ======================================================
   ETA COUNTDOWN
====================================================== */

function ETACountdown({ minutes }) {
  const [text, setText] = useState("");

  useEffect(() => {
    if (!minutes) return;

    const tick = () => {
      const diff = minutes * 60 * 1000;
      const m = Math.max(Math.floor(diff / 60000), 0);
      setText(m <= 0 ? "Arriving soon" : `${m} min`);
    };

    tick();
    const t = setInterval(tick, 60000);
    return () => clearInterval(t);
  }, [minutes]);

  return (
    <div className="bg-accent/10 rounded-xl p-4 text-center">
      <div className="text-2xl font-bold text-accent">{text}</div>
      <div className="text-sm text-muted">Estimated delivery</div>
    </div>
  );
}

/* ======================================================
   MAIN PAGE
====================================================== */

export default function OrderDetails() {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [order, setOrder] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  if (!isAuthenticated) {
    return <Navigate to="/signup" replace />;
  }

  /* ================= FETCH ORDER ================= */
  useEffect(() => {
    if (!orderId) return;

    setLoading(true);
    setError("");

    api
      .get(`/orders/${orderId}/detail/`)
      .then((res) => {
        setOrder(res);
        setStatus({
          status: res.status,
          eta_minutes: res.eta_minutes,
        });
      })
      .catch(() => {
        setError("Unable to load order");
      })
      .finally(() => setLoading(false));
  }, [orderId]);

  /* ================= POLL STATUS ONLY ================= */
  useEffect(() => {
    if (!orderId) return;

    const poll = () => {
      api
        .get(`/orders/${orderId}/status/`)
        .then(setStatus)
        .catch(() => {});
    };

    poll();
    const t = setInterval(poll, 15000);
    return () => clearInterval(t);
  }, [orderId]);

  /* ================= STATES ================= */
  if (loading) return <div className="p-6 text-muted">Loading order…</div>;

  if (error)
    return (
      <div className="p-6 space-y-4">
        <p className="text-red-400">{error}</p>
        <button className="btn" onClick={() => navigate("/my-orders")}>
          Back to Orders
        </button>
      </div>
    );

  const statusIndex = getStatusIndex(status?.status);

  /* ================= UI ================= */
  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      {/* HEADER */}
      <div className="bg-card p-5 rounded-2xl border">
        <div className="flex justify-between">
          <div>
            <h1 className="text-xl font-bold">
              Order #{order.order_number}
            </h1>
            <p className="text-sm text-muted">
              {new Date(order.created_at).toLocaleString()}
            </p>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-accent">
              ₹{order.total_amount}
            </div>
            <div className="text-xs text-muted">
              {order.payment_method}
            </div>
          </div>
        </div>
      </div>

      {/* STATUS */}
      {status && (
        <div className="bg-card p-6 rounded-2xl border space-y-6">
          <h3 className="font-semibold">Order Status</h3>

          {/* Progress */}
          <div>
            <div className="flex justify-between mb-2 text-sm">
              <span>Progress</span>
              <span className="text-muted">
                {STATUS_FLOW[statusIndex]?.label}
              </span>
            </div>

            <div className="relative">
              <div className="h-3 bg-subtle rounded-full">
                <motion.div
                  className="h-3 bg-accent rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${getProgressPercent(status.status)}%` }}
                />
              </div>

              <div className="absolute -top-1 left-0 right-0 flex justify-between">
                {STATUS_FLOW.map((s, i) => {
                  const Icon = s.icon;
                  const active = i <= statusIndex;

                  return (
                    <div
                      key={s.key}
                      className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        active ? `${s.bg} text-white` : "bg-muted text-muted"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ETA */}
          {status.eta_minutes && status.status !== "delivered" && (
            <ETACountdown minutes={status.eta_minutes} />
          )}
        </div>
      )}

      {/* TIMELINE */}
      {order.events?.length > 0 && (
        <div className="bg-card p-6 rounded-2xl border">
          <h3 className="font-semibold mb-4">Order Timeline</h3>
          <AnimatePresence>
            {order.events.map((e, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex gap-4 mb-4"
              >
                <ClockIcon className="w-5 h-5 text-accent mt-1" />
                <div>
                  <div className="font-medium">
                    {EVENT_LABELS[e.action] || e.action}
                  </div>
                  {e.note && (
                    <div className="text-sm text-muted">{e.note}</div>
                  )}
                  <div className="text-xs text-muted">
                    {new Date(e.created_at).toLocaleString()}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* FOOTER */}
      <div className="flex justify-between">
        <button className="btn" onClick={() => navigate("/my-orders")}>
          Back
        </button>
        {status?.status === "delivered" && (
          <button className="btn btn-primary" onClick={() => navigate("/")}>
            Order Again
          </button>
        )}
      </div>
    </div>
  );
}
