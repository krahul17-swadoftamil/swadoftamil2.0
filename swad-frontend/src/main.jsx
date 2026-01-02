import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";

/* ================= CONTEXT PROVIDERS ================= */
import { ThemeProvider } from "./context/ThemeContext";
import { CartProvider } from "./context/CartContext";

/* ================= GLOBAL STYLES ================= */
import "./index.css";

/* ================= BOOTSTRAP APP ================= */
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <CartProvider>
          <App />
        </CartProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);
