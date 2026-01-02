import { useCart } from "../context/CartContext";

/* ======================================================
   AddonCard
   - Supports legacy `addon` or generic `item`
   - Compact mode for inline lists / modals
   - ERP-safe pricing & qty handling
====================================================== */

export default function AddonCard({ addon, item, compact = false }) {
  /* ---------------- NORMALIZE PAYLOAD ---------------- */
  const data = item ?? addon ?? {};

  const id = data.id;
  const name = data.name ?? "Untitled";
  const price =
    Number(data.selling_price ?? data.price ?? 0) || 0;
  const image = data.image ?? data.image_url ?? null;

  /* ---------------- CART ---------------- */
  const { cart, addAddon, updateAddonQty } = useCart();

  const cartItem = cart.addons?.find((a) => a.id === id);
  const qty = cartItem?.qty ?? 0;

  const add = () =>
    addAddon({
      id,
      name,
      selling_price: price, // canonical
      price,                // backward safety
      image,
    });

  const inc = () => updateAddonQty(id, qty + 1);
  const dec = () => updateAddonQty(id, qty - 1);

  /* ---------------- COMPACT VARIANT ---------------- */
  if (compact) {
    return (
      <div className="flex items-center justify-between w-full gap-3">

        {/* INFO */}
        <div className="flex items-center gap-3 min-w-0">
          {image && (
            <img
              src={image}
              alt={name}
              className="w-8 h-8 rounded object-cover flex-shrink-0"
            />
          )}

          <div className="min-w-0">
            <p className="text-sm text-primary truncate">
              {name}
            </p>
            <p className="text-xs text-muted">
              ₹ {price}
            </p>
          </div>
        </div>

        {/* ACTION */}
        {qty === 0 ? (
          <button
            onClick={add}
            className="btn-addon text-xs px-3 py-1"
          >
            + Add
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={dec}
              className="btn-secondary w-7 h-7 rounded-full"
            >
              −
            </button>

            <span className="text-sm font-semibold">
              {qty}
            </span>

            <button
              onClick={inc}
              className="btn-primary w-7 h-7 rounded-full"
            >
              +
            </button>
          </div>
        )}
      </div>
    );
  }

  /* ---------------- FULL CARD ---------------- */
  return (
    <div className="rounded-xl card-gradient border border-subtle flex items-center justify-between px-4 py-3">

      {/* INFO */}
      <div className="min-w-0">
        <p className="text-sm font-medium text-primary truncate">
          {name}
        </p>
        <p className="text-xs text-muted">
          <span className="text-accent-strong">₹</span> {price}
        </p>
      </div>

      {/* ACTION */}
      {qty === 0 ? (
        <button
          onClick={add}
          className="btn-addon text-sm px-4 py-1.5"
        >
          + Add
        </button>
      ) : (
        <div className="flex items-center gap-3">
          <button
            onClick={dec}
            className="btn-secondary w-8 h-8 rounded-full"
          >
            −
          </button>

          <span className="qty-pill text-sm font-semibold">
            {qty}
          </span>

          <button
            onClick={inc}
            className="btn-primary w-8 h-8 rounded-full"
          >
            +
          </button>
        </div>
      )}
    </div>
  );
}
