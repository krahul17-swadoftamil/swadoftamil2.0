import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy } from "react";

import Navbar from "./components/Navbar";
import CheckoutContainer from "./components/CheckoutContainer";
import FloatingCart from "./components/FloatingCart";

/* ================= LAZY PAGES ================= */
const Home = lazy(() => import("./pages/Home"));
const About = lazy(() => import("./pages/About"));
const Snacks = lazy(() => import("./pages/Snacks"));
const MyOrders = lazy(() => import("./pages/MyOrders"));
const OrderDetails = lazy(() => import("./pages/OrderDetails"));

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-app text-text">
      {/* ================= NAVBAR ================= */}
      <Navbar />

      {/* ================= CONTENT ================= */}
      <main className="flex-1">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/snacks" element={<Snacks />} />
            <Route path="/my-orders" element={<MyOrders />} />
            <Route path="/order/:id" element={<OrderDetails />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>

      {/* ================= GLOBAL CHECKOUT ================= */}
      <CheckoutContainer />
      <FloatingCart />
    </div>
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
