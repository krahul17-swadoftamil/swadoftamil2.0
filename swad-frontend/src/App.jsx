import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy, useEffect } from "react";

import Navbar from "./components/Navbar";
import CheckoutContainer from "./components/CheckoutContainer";
import FloatingCart from "./components/FloatingCart";

import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { JWTProvider, useJWT } from "./context/JWTContext";
import { setJWTTokenGetter } from "./api";

/* ================= LAZY PAGES ================= */
const Welcome = lazy(() => import("./pages/Welcome"));
const Home = lazy(() => import("./pages/Home"));
const Items = lazy(() => import("./pages/ItemsPage"));
const About = lazy(() => import("./pages/About"));
const Snacks = lazy(() => import("./pages/Snacks"));
const SubscriptionPage = lazy(() => import("./pages/SubscriptionPage"));
const MyOrders = lazy(() => import("./pages/MyOrders"));
const OrderDetails = lazy(() => import("./pages/OrderDetails"));
const MobileSignup = lazy(() => import("./pages/MobileSignup"));
const GoogleCallback = lazy(() => import("./pages/GoogleCallback"));

// Page loader component
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
    </div>
  );
}

// JWT initializer component
function JWTInitializer() {
  const { getValidAccessToken } = useJWT();

  useEffect(() => {
    // Set the JWT token getter for the API client
    setJWTTokenGetter(getValidAccessToken);
  }, [getValidAccessToken]);

  return null;
}

export default function App() {
  return (
    <JWTProvider>
      <AuthProvider>
        <CartProvider>
          <JWTInitializer />
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
                  <Route path="/items" element={<Items />} />
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
  </JWTProvider>
  );
}
