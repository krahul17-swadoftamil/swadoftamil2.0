import {
  createContext,
  useContext,
  useReducer,
  useMemo,
  useEffect,
  useRef,
} from "react";
import { api } from "../api";

/* ======================================================
   CartContext — FINAL (Order API Aligned)
====================================================== */

const CartContext = createContext(null);

/* ================= INITIAL STATE ================= */

const initialState = {
  combos: [],
  items: [],
  snacks: [],
  checkoutOpen: false,
  isPlacingOrder: false,
  lastAddedItem: null, // For animation
};

/* ================= HELPERS ================= */

const normalize = (obj) => ({
  id: obj.id,
  name: obj.name,
  price: Math.round(Number(obj.selling_price ?? obj.price ?? 0)),
  image: obj.image ?? null,
});

const upsert = (list, item, qty) => {
  if (qty <= 0) return list.filter((x) => x.id !== item.id);
  const exists = list.find((x) => x.id === item.id);
  return exists
    ? list.map((x) => (x.id === item.id ? { ...x, qty } : x))
    : [...list, { ...item, qty }];
};

const inc = (list, id) =>
  list.map((x) => (x.id === id ? { ...x, qty: x.qty + 1 } : x));

const dec = (list, id) =>
  list
    .map((x) => (x.id === id ? { ...x, qty: x.qty - 1 } : x))
    .filter((x) => x.qty > 0);

/* ================= REDUCER ================= */

function reducer(state, action) {
  switch (action.type) {
    /* COMBOS */
    case "SET_COMBO":
      return { ...state, combos: upsert(state.combos, action.item, action.qty) };
    case "INC_COMBO":
      return { ...state, combos: inc(state.combos, action.id) };
    case "DEC_COMBO":
      return { ...state, combos: dec(state.combos, action.id) };
    case "REMOVE_COMBO":
      return { ...state, combos: state.combos.filter((x) => x.id !== action.id) };

    /* ITEMS */
    case "SET_ITEM":
      return { ...state, items: upsert(state.items, action.item, action.qty) };
    case "INC_ITEM":
      return { ...state, items: inc(state.items, action.id) };
    case "DEC_ITEM":
      return { ...state, items: dec(state.items, action.id) };
    case "REMOVE_ITEM":
      return { ...state, items: state.items.filter((x) => x.id !== action.id) };

    /* SNACKS */
    case "SET_SNACK":
      return { ...state, snacks: upsert(state.snacks, action.item, action.qty) };
    case "INC_SNACK":
      return { ...state, snacks: inc(state.snacks, action.id) };
    case "DEC_SNACK":
      return { ...state, snacks: dec(state.snacks, action.id) };
    case "REMOVE_SNACK":
      return { ...state, snacks: state.snacks.filter((x) => x.id !== action.id) };

    /* CHECKOUT */
    case "OPEN_CHECKOUT":
      return { ...state, checkoutOpen: true };
    case "CLOSE_CHECKOUT":
      return { ...state, checkoutOpen: false };

    /* ORDER */
    case "ORDER_START":
      return { ...state, isPlacingOrder: true };
    case "ORDER_SUCCESS":
      return { 
        ...initialState, 
        checkoutOpen: state.checkoutOpen // Keep checkout open for success feedback
      };
    case "ORDER_END":
      return { ...state, isPlacingOrder: false };

    /* ANIMATION */
    case "ITEM_ADDED":
      return { ...state, lastAddedItem: action.item };
    case "CLEAR_ANIMATION":
      return { ...state, lastAddedItem: null };

    default:
      return state;
  }
}

/* ================= PROVIDER ================= */

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const saveTimer = useRef(null);

  /* ---------- SELECTORS ---------- */

  const itemCount = useMemo(
    () =>
      [...state.combos, ...state.items, ...state.snacks].reduce(
        (s, x) => s + x.qty,
        0
      ),
    [state]
  );

  const total = useMemo(
    () =>
      [...state.combos, ...state.items, ...state.snacks].reduce(
        (s, x) => s + x.price * x.qty,
        0
      ),
    [state]
  );

  // Free delivery threshold
  const FREE_DELIVERY_THRESHOLD = 200;
  const freeDeliveryProgress = useMemo(() => {
    if (total >= FREE_DELIVERY_THRESHOLD) return null;
    return FREE_DELIVERY_THRESHOLD - total;
  }, [total]);

  // Suggested add-ons (simple logic - could be more sophisticated)
  const suggestedAddons = useMemo(() => {
    if (!state.snacks.length && total > 50) {
      return [
        { type: 'snack', name: 'Chutney', price: 25, reason: 'Perfect with idlis' },
        { type: 'snack', name: 'Extra Sambar', price: 30, reason: 'More authentic taste' }
      ];
    }
    return [];
  }, [state.snacks, total]);

  /* ---------- ADD WITH ANIMATION ---------- */

  const addCombo = (combo, qty = 1) => {
    dispatch({ type: "SET_COMBO", item: normalize(combo), qty });
    dispatch({ type: "ITEM_ADDED", item: normalize(combo) });
  };

  const addItem = (item, qty = 1) => {
    dispatch({ type: "SET_ITEM", item: normalize(item), qty });
    dispatch({ type: "ITEM_ADDED", item: normalize(item) });
  };

  const addSnack = (snack, qty = 1) => {
    dispatch({ type: "SET_SNACK", item: normalize(snack), qty });
    dispatch({ type: "ITEM_ADDED", item: normalize(snack) });
  };

  /* ---------- CHECKOUT ---------- */

  const openCheckout = () => dispatch({ type: "OPEN_CHECKOUT" });
  const closeCheckout = () => dispatch({ type: "CLOSE_CHECKOUT" });

  /* ---------- PLACE ORDER ---------- */

  const placeOrderAsync = async (customer) => {
    // ✔ Guard: prevent duplicate orders
    if (!itemCount || state.isPlacingOrder) {
      throw new Error("Order is already being placed");
    }

    dispatch({ type: "ORDER_START" });

    try {
      const payload = {
        combos: state.combos.map((c) => ({
          id: c.id,
          quantity: c.qty,
        })),
        items: state.items.map((i) => ({
          id: i.id,
          quantity: i.qty,
        })),
        snacks: state.snacks.map((s) => ({
          snack_id: s.id,
          quantity: s.qty,
        })),
        payment_method: "cod",
        customer: {
          phone: customer.phone,          // 🔒 mandatory
          name: customer.name || "",
          email: customer.email || "",
          address: customer.address || "",
        },
      };

      const order = await api.post("/orders/", payload);
      
      // ✔ Clear cart IMMEDIATELY on success
      dispatch({ type: "ORDER_SUCCESS" });
      
      return order;
    } catch (error) {
      // ✔ Don't clear cart on error—allow retry
      dispatch({ type: "ORDER_END" });
      throw error;
    }
  };

  /* ---------- OPTIONAL CART AUTOSAVE ---------- */

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);

    saveTimer.current = setTimeout(() => {
      if (!itemCount || state.isPlacingOrder) return;

      api.post("/orders/cart/", {
        total_amount: total,
        lines: [
          ...state.combos.map((c) => ({
            type: "combo",
            combo: c.id,
            quantity: c.qty,
            unit_price: c.price,
          })),
          ...state.items.map((i) => ({
            type: "item",
            item: i.id,
            quantity: i.qty,
            unit_price: i.price,
          })),
          ...state.snacks.map((s) => ({
            type: "snack",
            snack_id: s.id,
            snack_name: s.name,
            quantity: s.qty,
            unit_price: s.price,
          })),
        ],
      });
    }, 800);

    return () => clearTimeout(saveTimer.current);
  }, [state, total, itemCount]);

  /* ---------- CONTEXT API ---------- */

  const value = {
    cart: state,

    /* Add */
    addCombo,
    addItem,
    addSnack,

    /* Modify */
    incCombo: (id) => dispatch({ type: "INC_COMBO", id }),
    decCombo: (id) => dispatch({ type: "DEC_COMBO", id }),
    removeCombo: (id) => dispatch({ type: "REMOVE_COMBO", id }),

    incItem: (id) => dispatch({ type: "INC_ITEM", id }),
    decItem: (id) => dispatch({ type: "DEC_ITEM", id }),
    removeItem: (id) => dispatch({ type: "REMOVE_ITEM", id }),

    incSnack: (id) => dispatch({ type: "INC_SNACK", id }),
    decSnack: (id) => dispatch({ type: "DEC_SNACK", id }),
    removeSnack: (id) => dispatch({ type: "REMOVE_SNACK", id }),

    /* Checkout */
    checkoutOpen: state.checkoutOpen,
    openCheckout,
    closeCheckout,

    /* Totals */
    itemCount,
    total,

    /* Free Delivery */
    freeDeliveryProgress,
    freeDeliveryThreshold: FREE_DELIVERY_THRESHOLD,

    /* Suggestions */
    suggestedAddons,

    /* Animation */
    lastAddedItem: state.lastAddedItem,
    clearAnimation: () => dispatch({ type: "CLEAR_ANIMATION" }),

    /* Order */
    placeOrderAsync,
    isPlacingOrder: state.isPlacingOrder,
    clearCart: () => dispatch({ type: "ORDER_SUCCESS" }),
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
}

/* ================= HOOK ================= */

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error("useCart must be used inside CartProvider");
  }
  return ctx;
}
