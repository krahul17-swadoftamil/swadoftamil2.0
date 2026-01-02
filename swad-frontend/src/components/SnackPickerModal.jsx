import { useEffect } from "react";
import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";

/* ======================================================
   SnackPickerModal — Snack Upsell
   • Simple
   • Optional
   • Fast add
====================================================== */

export default function SnackPickerModal({
  open,
  snacks = [],
  onClose,
}) {
  const { addSnack } = useCart();

  /* ================= ESC TO CLOSE ================= */
  useEffect(() => {
    if (!open) return;
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="
          w-full sm:max-w-3xl
          bg-card rounded-t-3xl sm:rounded-2xl
          overflow-hidden flex flex-col
        "
      >
        {/* ================= HEADER ================= */}
        <div className="flex items-center justify-between p-4 border-b border-subtle">
          <h3 className="text-lg font-semibold">
            Add snacks
          </h3>
          <button
            onClick={onClose}
            className="text-muted hover:text-text"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* ================= CONTENT ================= */}
        <div className="p-4 grid grid-cols-2 sm:grid-cols-3 gap-4 overflow-y-auto">
          {snacks.length === 0 ? (
            <div className="col-span-full text-center text-muted text-sm">
              No snacks available
            </div>
          ) : (
            snacks.map((snack) => {
              const image = resolveMediaUrl(snack.image);
              const price = Number(snack.selling_price || 0);

              return (
                <div
                  key={snack.id}
                  className="
                    relative rounded-xl bg-surface
                    border border-subtle
                    overflow-hidden flex flex-col
                  "
                >
                  {/* IMAGE */}
                  <div className="h-28 flex items-center justify-center bg-black/5">
                    {image && (
                      <img
                        src={image}
                        alt={snack.name}
                        className="max-h-full p-2 object-contain"
                      />
                    )}
                  </div>

                  {/* INFO */}
                  <div className="p-3 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="text-sm font-semibold">
                        {snack.name}
                      </div>
                      <div className="text-xs text-muted">
                        ₹{price}
                      </div>
                    </div>

                    <button
                      onClick={() => addSnack(snack)}
                      disabled={!snack.in_stock}
                      className="mt-2 btn-primary w-full text-sm"
                    >
                      {snack.in_stock ? "Add" : "Out of stock"}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* ================= FOOTER ================= */}
        <div className="border-t border-subtle p-3 text-xs text-muted text-center">
          Snacks are optional add-ons · Do not affect combo contents
        </div>
      </div>
    </div>
  );
}
