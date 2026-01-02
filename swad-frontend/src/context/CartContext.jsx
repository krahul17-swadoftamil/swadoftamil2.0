import {
  createContext,
  useContext,
  useMemo,
  useReducer,
  useEffect,
  useRef,
  useState,
} from "react";
import { api } from "../api";

/* ======================================================
   CartContext — ERP-Grade (FINAL, CLEAN)
====================================================== */

const CartContext = createContext(null);

/* ======================================================
   INITIAL STATE
====================================================== */

const initialState = {
  combos: [],
  items: [],
  snacks: [],
  checkoutOpen: false,
  isPlacingOrder: false,
};

/* ======================================================
   HELPERS
====================================================== */

function normalize(obj) {
  return {
    id: obj.id,
    name: obj.name,
    price: Math.round(
      Number(obj.selling_price ?? obj.price ?? 0)
    ),
    image: obj.image ?? null,
  };
}

function upsert(list, item, qty) {
  if (qty <= 0) {
    return list.filter((x) => x.id !== item.id);
  }

  const exists = list.find((x) => x.id === item.id);
  if (exists) {
    return list.map((x) =>
      x.id === item.id ? { ...x, qty } : x
    );
  }

  return [...list, { ...item, qty }];
}

function inc(list, id) {
  return list.map((x) =>
    x.id === id ? { ...x, qty: x.qty + 1 } : x
  );
}

function dec(list, id) {
  return list
    .map((x) =>
      x.id === id ? { ...x, qty: x.qty - 1 } : x
    )
    .filter((x) => x.qty > 0);
}

/* ======================================================
   REDUCER
====================================================== */

function reducer(state, action) {
  switch (action.type) {
    /* ===== COMBOS ===== */
    case "SET_COMBO":
      return {
        ...state,
        combos: upsert(
          state.combos,
          action.item,
          action.qty
        ),
      };
    case "INC_COMBO":
      return { ...state, combos: inc(state.combos, action.id) };
    case "DEC_COMBO":
      return { ...state, combos: dec(state.combos, action.id) };
    case "REMOVE_COMBO":
      return {
        ...state,
        combos: state.combos.filter((c) => c.id !== action.id),
      };

    /* ===== ITEMS ===== */
    case "SET_ITEM":
      return {
        ...state,
        items: upsert(
          state.items,
          action.item,
          action.qty
        ),
      };
    case "INC_ITEM":
      return { ...state, items: inc(state.items, action.id) };
    case "DEC_ITEM":
      return { ...state, items: dec(state.items, action.id) };
    case "REMOVE_ITEM":
      return {
        ...state,
        items: state.items.filter((i) => i.id !== action.id),
      };

    /* ===== SNACKS ===== */
    case "SET_SNACK":
      return {
        ...state,
        snacks: upsert(
          state.snacks,
          action.item,
          action.qty
        ),
      };
    case "INC_SNACK":
      return { ...state, snacks: inc(state.snacks, action.id) };
    case "DEC_SNACK":
      return { ...state, snacks: dec(state.snacks, action.id) };
    case "REMOVE_SNACK":
      return {
        ...state,
        snacks: state.snacks.filter((s) => s.id !== action.id),
      };

    /* ===== CHECKOUT ===== */
    case "OPEN_CHECKOUT":
      return { ...state, checkoutOpen: true };
    case "CLOSE_CHECKOUT":
      return { ...state, checkoutOpen: false };

    /* ===== ORDER ===== */
    case "ORDER_START":
      return { ...state, isPlacingOrder: true };
    case "ORDER_SUCCESS":
      return { ...initialState };
    case "ORDER_END":
      return { ...state, isPlacingOrder: false };

    default:
      return state;
  }
}

/* ======================================================
   PROVIDER
====================================================== */

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(
    reducer,
    initialState
  );

  const [savedCartMeta, setSavedCartMeta] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("swad_cart_meta")) || {};
    } catch {
      return {};
    }
  });
  const saveTimer = useRef();

  /* ================= COMBOS ================= */

  const addCombo = (combo, qty = 1) => {
    const item = normalize(combo);
    const existing = state.combos.find(
      (c) => String(c.id) === String(item.id)
    );
    const newQty = (existing?.qty || 0) + qty;

    dispatch({
      type: "SET_COMBO",
      item,
      qty: newQty,
    });
  };

  // Set combo to an exact quantity (used by some components)
  const setCombo = (comboObj, qty = 1) => {
    const item = normalize(comboObj);
    const q = Number(qty) || 0;
    dispatch({ type: "SET_COMBO", item, qty: q });
  };

  const incCombo = (id) =>
    dispatch({ type: "INC_COMBO", id });
  const decCombo = (id) =>
    dispatch({ type: "DEC_COMBO", id });
  const removeCombo = (id) =>
    dispatch({ type: "REMOVE_COMBO", id });

  /* ================= ITEMS ================= */

  const addItem = (itemObj, qty = 1) => {
    const item = normalize(itemObj);
    const existing = state.items.find(
      (i) => String(i.id) === String(item.id)
    );
    const newQty = (existing?.qty || 0) + qty;

    dispatch({
      type: "SET_ITEM",
      item,
      qty: newQty,
    });
  };

  const incItem = (id) =>
    dispatch({ type: "INC_ITEM", id });
  const decItem = (id) =>
    dispatch({ type: "DEC_ITEM", id });
  const removeItem = (id) =>
    dispatch({ type: "REMOVE_ITEM", id });

  /* ================= SNACKS ================= */

  const addSnack = (snackObj, qty = 1) => {
    const item = normalize(snackObj);
    const existing = state.snacks.find(
      (s) => String(s.id) === String(item.id)
    );
    const newQty = (existing?.qty || 0) + qty;

    dispatch({
      type: "SET_SNACK",
      item,
      qty: newQty,
    });
  };

  const incSnack = (id) =>
    dispatch({ type: "INC_SNACK", id });
  const decSnack = (id) =>
    dispatch({ type: "DEC_SNACK", id });
  const removeSnack = (id) =>
    dispatch({ type: "REMOVE_SNACK", id });

  /* ================= SELECTORS ================= */

  const itemCount = useMemo(() => {
    const sum = (arr) =>
      arr.reduce((s, i) => s + i.qty, 0);
    return (
      sum(state.combos) +
      sum(state.items) +
      sum(state.snacks)
    );
  }, [state]);

  const total = useMemo(() => {
    const sum = (arr) =>
      arr.reduce((s, i) => s + i.price * i.qty, 0);
    return (
      sum(state.combos) +
      sum(state.items) +
      sum(state.snacks)
    );
  }, [state]);

  /* ================= CHECKOUT ================= */

  const openCheckout = () =>
    dispatch({ type: "OPEN_CHECKOUT" });
  const closeCheckout = () =>
    dispatch({ type: "CLOSE_CHECKOUT" });

  /* ================= ORDER ================= */

  // Accept optional `customer` object: { name, phone, email, address }
  const placeOrderAsync = async (customer = null) => {
    if (!itemCount || state.isPlacingOrder) return;

    dispatch({ type: "ORDER_START" });

    try {
      const payload = {
        combos: state.combos.map((c) => ({
          id: c.id,
          quantity: c.qty,
        })),
        items: state.items.map((i) => ({
          item_id: i.id,
          quantity: i.qty,
        })),
        snacks: state.snacks.map((s) => ({
          snack_id: s.id,
          quantity: s.qty,
        })),
      };

      if (customer) {
        payload.customer = {
          name: customer.name || "",
          phone: customer.phone || "",
          email: customer.email || "",
          address: customer.address || "",
        };
      }

      const res = await api.post("/orders/", payload);
      dispatch({ type: "ORDER_SUCCESS" });
      return res;
    } finally {
      dispatch({ type: "ORDER_END" });
    }
  };

  /* ================= CART PERSISTENCE ================= */
  function genSessionKey() {
    return `sess-${Math.random().toString(36).slice(2, 10)}`;
  }

  function buildCartPayload() {
    const payload = {
      id: savedCartMeta.id,
      session_key: savedCartMeta.session_key || undefined,
      total_amount: total,
      metadata: {},
      lines: [],
    };

    (state.combos || []).forEach((c) => {
      payload.lines.push({
        type: "combo",
        combo: c.id,
        quantity: c.qty,
        unit_price: c.price,
      });
    });

    (state.items || []).forEach((i) => {
      payload.lines.push({
        type: "item",
        prepared_item: i.id,
        quantity: i.qty,
        unit_price: i.price,
      });
    });

    (state.snacks || []).forEach((s) => {
      payload.lines.push({
        type: "snack",
        snack_id: s.id,
        snack_name: s.name,
        quantity: s.qty,
        unit_price: s.price,
      });
    });

    return payload;
  }

  const saveCart = async () => {
    try {
      // Ensure we have a session key
      if (!savedCartMeta.session_key) {
        const sk = genSessionKey();
        const meta = { ...(savedCartMeta || {}), session_key: sk };
        setSavedCartMeta(meta);
        localStorage.setItem("swad_cart_meta", JSON.stringify(meta));
      }

      const payload = buildCartPayload();
      const res = await api.post("/orders/cart/", payload);

      if (res?.id || res?.session_key) {
        const meta = { ...(savedCartMeta || {}), id: res.id, session_key: res.session_key };
        setSavedCartMeta(meta);
        localStorage.setItem("swad_cart_meta", JSON.stringify(meta));
      }

      return res;
    } catch (err) {
      // fail silently for UX; console for debugging
      console.error("Failed to save cart:", err);
      return null;
    }
  };

  const loadCart = async (opts = {}) => {
    try {
      const meta = savedCartMeta || {};
      const session = opts.session || meta.session_key;
      const customer = opts.customer;

      if (!session && !customer) return null;

      const q = session ? { session } : { customer };
      const res = await api.get("/orders/cart/", q);
      return res;
    } catch (err) {
      console.error("Failed to load cart:", err);
      return null;
    }
  };

  const clearSavedCart = async () => {
    try {
      const meta = savedCartMeta || {};
      if (meta.id) {
        await api.delete(`/orders/cart/?id=${meta.id}`);
      }
    } catch (err) {
      console.error(err);
    }
    setSavedCartMeta({});
    localStorage.removeItem("swad_cart_meta");
  };

  // Auto-save (debounced) when cart changes
  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      // do not auto-save when placing order or empty
      if (state.isPlacingOrder) return;
      saveCart();
    }, 1000);

    return () => clearTimeout(saveTimer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(state.combos), JSON.stringify(state.items), JSON.stringify(state.snacks), total]);

  /* ================= PUBLIC API ================= */

  const value = {
    cart: state,

    /* Combos */
    addCombo,
    setCombo,
    incCombo,
    decCombo,
    removeCombo,

    /* Items */
    addItem,
    incItem,
    decItem,
    removeItem,

    /* Snacks */
    addSnack,
    incSnack,
    decSnack,
    removeSnack,

    /* Checkout */
    checkoutOpen: state.checkoutOpen,
    openCheckout,
    closeCheckout,

    /* Totals */
    itemCount,
    total,

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

/* ======================================================
   HOOK
====================================================== */

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error(
      "useCart must be used inside CartProvider"
    );
  }
  return ctx;
}
