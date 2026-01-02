import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";

/* ======================================================
   OrderDetails — Secure Order View (POST-based)
====================================================== */

export default function OrderDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    setLoading(true);
    setError("");

    api
      .post("/orders/detail/", { order_id: id }) // 🔥 POST, not GET
      .then((res) => {
        setOrder(res);
      })
      .catch((err) => {
        setError(
          err?.message ||
            "Unable to fetch order details"
        );
        setOrder(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  /* ================= STATES ================= */

  if (loading) {
    return (
      <div className="p-6 text-muted">
        Loading order details…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-3">
        <div className="text-red-500">{error}</div>
        <button
          className="btn"
          onClick={() => navigate("/my-orders")}
        >
          Back to My Orders
        </button>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="p-6">
        Order not found
      </div>
    );
  }

  /* ================= UI ================= */

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* HEADER */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-xl font-semibold">
            Order #{order.order_number || order.id}
          </h1>
          <div className="text-sm text-muted">
            {new Date(order.created_at).toLocaleString()}
          </div>
        </div>

        <div className="text-right">
          <div className="text-lg font-bold text-accent">
            ₹{order.total_amount}
          </div>
          <div className="text-xs text-muted">
            {order.status_display || order.status}
          </div>
        </div>
      </div>

      {/* CUSTOMER */}
      <div className="bg-card rounded-xl p-4">
        <div className="font-medium mb-1">
          Customer
        </div>
        <div className="text-sm">
          {order.customer_name || "—"}
        </div>
        <div className="text-sm text-muted">
          {order.customer_phone}
        </div>
      </div>

      {/* COMBOS */}
      {order.order_combos?.length > 0 && (
        <Section title="Combos">
          {order.order_combos.map((c) => (
            <Row
              key={c.id}
              name={c.combo_name}
              qty={c.quantity}
            />
          ))}
        </Section>
      )}

      {/* ITEMS */}
      {order.order_items?.length > 0 && (
        <Section title="Items">
          {order.order_items.map((i) => (
            <Row
              key={i.id}
              name={i.prepared_item_name}
              qty={i.quantity}
            />
          ))}
        </Section>
      )}

      {/* SNACKS */}
      {order.order_snacks?.length > 0 && (
        <Section title="Snacks">
          {order.order_snacks.map((s, idx) => (
            <Row
              key={idx}
              name={s.snack_name}
              qty={s.quantity}
              price={s.unit_price}
            />
          ))}
        </Section>
      )}

      {/* FOOTER */}
      <div className="flex justify-between pt-4">
        <button
          className="btn"
          onClick={() => navigate("/my-orders")}
        >
          Back
        </button>
      </div>
    </div>
  );
}

/* ================= REUSABLE ================= */

function Section({ title, children }) {
  return (
    <div className="bg-card rounded-xl p-4">
      <div className="font-medium mb-2">
        {title}
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Row({ name, qty, price }) {
  return (
    <div className="flex justify-between text-sm">
      <div>
        {name} × {qty}
      </div>
      {price != null && (
        <div className="text-muted">
          ₹{price}
        </div>
      )}
    </div>
  );
}
