import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy } from "react";

import Navbar from "./components/Navbar";
import CheckoutContainer from "./components/CheckoutContainer";
import FloatingCart from "./components/FloatingCart";

import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";

/* ================= LAZY PAGES ================= */
const Welcome = lazy(() => import("./pages/Welcome"));
const Home = lazy(() => import("./pages/Home"));
const About = lazy(() => import("./pages/About"));
const Snacks = lazy(() => import("./pages/Snacks"));
const SubscriptionPage = lazy(() => import("./pages/SubscriptionPage"));
const MyOrders = lazy(() => import("./pages/MyOrders"));
const OrderDetails = lazy(() => import("./pages/OrderDetails"));
const MobileSignup = lazy(() => import("./pages/MobileSignup"));
const GoogleCallback = lazy(() => import("./pages/GoogleCallback"));

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <div className="min-h-screen flex flex-col bg-app text-text">
          {/* ================= NAVBAR ================= */}
          <Navbar />

          {/* ================= MAIN CONTENT ================= */}
          <main className="flex-1">
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* ENTRY POINT */}
                <Route path="/" element={<Navigate to="/welcome" replace />} />
                <Route path="/welcome" element={<Welcome />} />

                {/* MAIN APP */}
                <Route path="/home" element={<Home />} />
                <Route path="/about" element={<About />} />
                <Route path="/snacks" element={<Snacks />} />
                <Route path="/subscription" element={<SubscriptionPage />} />

                {/* AUTH */}
                <Route path="/signup" element={<MobileSignup />} />
                <Route
                  path="/auth/google/callback"
                  element={<GoogleCallback />}
                />

                {/* ORDERS */}
                <Route path="/my-orders" element={<MyOrders />} />
                <Route
                  path="/orders/:orderId"
                  element={<OrderDetails />}
                />

                {/* FALLBACK */}
                <Route path="*" element={<Navigate to="/welcome" replace />} />
              </Routes>
            </Suspense>
          </main>

          {/* ================= GLOBAL OVERLAYS ================= */}
          <CheckoutContainer />
          <FloatingCart />
        </div>
      </CartProvider>
    </AuthProvider>
  );
}

/* ================= PAGE LOADER ================= */
function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="h-10 w-10 rounded-full border-4 border-accent/30 border-t-accent animate-spin" />
    </div>
  );
}
