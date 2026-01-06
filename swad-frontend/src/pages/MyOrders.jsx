import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";
import AccountModal from "../components/AccountModal";

/* ======================================================
   MyOrders — STABLE AUTH SAFE VERSION
====================================================== */

export default function MyOrders() {
  const navigate = useNavigate();
  const { user, isAuthenticated, checking } = useAuth();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  /* ================= AUTH CHECK ================= */
  useEffect(() => {
    if (!isAuthenticated) navigate("/signup");
  }, [isAuthenticated, navigate]);

  /* ================= FETCH ORDERS ================= */
  useEffect(() => {
    if (!checking && isAuthenticated && user?.phone) {
      fetchOrders(user.phone);
    }
  }, [checking, isAuthenticated, user?.phone]);

  const fetchOrders = async (phone) => {
    setLoading(true);
    setSearched(true);

    try {
      const res = await api.post("/orders/search/", { phone });
      setOrders(Array.isArray(res) ? res : res?.results || []);
    } catch {
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  /* ================= LOADING STATE ================= */
  if (checking) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="h-10 w-10 rounded-full border-4 border-accent/30 border-t-accent animate-spin" />
      </div>
    );
  }

  /* ================= AUTHENTICATED UI ================= */
  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* HEADER */}
      <div className="mb-6 p-4 bg-card rounded-xl border border-subtle">
        <h1 className="text-xl font-semibold mb-1">My Orders</h1>
        <div className="text-sm text-muted">
          <div><strong>{user?.name || "Customer"}</strong></div>
          <div>{user?.phone}</div>
          {user?.email && <div>{user.email}</div>}
        </div>
      </div>

      {/* LOADING */}
      {loading && (
        <div className="text-center py-10 text-muted">
          <div className="h-8 w-8 mx-auto rounded-full border-4 border-accent/30 border-t-accent animate-spin mb-3" />
          Loading orders…
        </div>
      )}

      {/* EMPTY */}
      {!loading && searched && orders.length === 0 && (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">📦</div>
          <p className="text-muted">No orders found</p>
        </div>
      )}

      {/* LIST */}
      <div className="space-y-4">
        {orders.map((o) => (
          <div
            key={o.id}
            className="rounded-xl border border-subtle p-4 bg-card"
          >
            <div className="flex justify-between mb-2">
              <div>
                <div className="font-semibold">
                  Order #{o.order_number || o.id.slice(-6)}
                </div>
                <div className="text-xs text-muted">
                  {new Date(o.created_at).toLocaleString()}
                </div>
              </div>

              <div className="text-right">
                <div className="font-bold text-accent">
                  ₹{o.total_amount}
                </div>
                <div className="text-xs text-muted">
                  {o.status_display || o.status}
                </div>
              </div>
            </div>

            <button className="text-xs text-accent hover:underline">
              View Details
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
