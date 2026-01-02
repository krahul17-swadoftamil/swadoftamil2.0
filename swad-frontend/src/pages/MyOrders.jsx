import { useState } from "react";
import { api } from "../api";

/* ======================================================
   MyOrders — Order History Lookup
====================================================== */

export default function MyOrders() {
  const [phone, setPhone] = useState("");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const fetchOrders = async () => {
    if (!phone.trim()) {
      alert("Enter phone number to search orders");
      return;
    }

    setLoading(true);
    setSearched(true);

    try {
      // 🔥 POST-based search (backend-safe)
      const res = await api.post("/orders/search/", {
        phone: phone.trim(),
      });

      const list =
        Array.isArray(res) ? res : res?.results || [];

      setOrders(list);
    } catch (err) {
      alert(err?.message || "Failed to fetch orders");
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-4">
        My Orders
      </h1>

      {/* SEARCH */}
      <div className="flex gap-2 mb-6">
        <input
          className="input flex-1"
          placeholder="Enter phone number"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <button
          className="btn-primary"
          onClick={fetchOrders}
          disabled={loading}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {/* STATES */}
      {loading && (
        <div className="text-muted">Loading orders…</div>
      )}

      {!loading && searched && orders.length === 0 && (
        <div className="text-muted text-center">
          No orders found for this number
        </div>
      )}

      {/* LIST */}
      <ul className="space-y-4">
        {orders.map((o) => (
          <li
            key={o.id}
            className="rounded-xl border border-subtle p-4 bg-card"
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="font-semibold">
                  Order #{o.id}
                </div>
                <div className="text-xs text-muted">
                  {new Date(o.created_at).toLocaleString()}
                </div>
                <div className="text-sm mt-1">
                  Status:{" "}
                  <span className="font-medium">
                    {o.status_display || o.status}
                  </span>
                </div>
                <div className="text-sm text-muted">
                  Items: {o.total_items}
                </div>
              </div>

              <div className="text-right">
                <div className="text-lg font-bold text-accent">
                  ₹{o.total_amount}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
