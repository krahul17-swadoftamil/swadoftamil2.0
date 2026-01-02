/* ======================================================
   SERVICES — SWAD OF TAMIL
   Informational • Trust-building • Non-ordering
====================================================== */

import { Link } from "react-router-dom";

export default function Services() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white pb-24">

      {/* ================= HERO ================= */}
      <section className="px-6 pt-12 pb-10 text-center relative">
        <h1 className="text-4xl font-bold tracking-wide bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
          How We Serve You
        </h1>

        <p className="mt-3 text-gray-300 text-sm max-w-md mx-auto">
          Simple, disciplined systems to deliver authentic Tamil breakfast.
        </p>
      </section>

      {/* ================= SERVICES ================= */}
      <section className="px-6 py-10">
        <div className="max-w-md mx-auto space-y-6">

          {[
            {
              icon: "🏪",
              title: "Pickup Points",
              desc: "Order ahead and collect fresh breakfast from convenient locations."
            },
            {
              icon: "🚚",
              title: "Home Delivery",
              desc: "Fast delivery with premium packaging to retain heat and taste."
            },
            {
              icon: "👥",
              title: "Fixed Combos",
              desc: "Disciplined portions — Solo, Sharing, and Family boxes."
            },
            {
              icon: "🏭",
              title: "Central Kitchen",
              desc: "Hygienic, SOP-driven preparation for consistent taste."
            }
          ].map((s, i) => (
            <div key={i} className="bg-gray-800/50 p-6 rounded-2xl">
              <div className="flex items-center gap-4 mb-2">
                <div className="text-2xl">{s.icon}</div>
                <h3 className="text-lg font-semibold">{s.title}</h3>
              </div>
              <p className="text-gray-300 text-sm">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="px-6 py-10 text-center">
        <Link
          to="/"
          className="inline-block px-8 py-3 rounded-full bg-accent text-black font-semibold"
        >
          View Menu & Order →
        </Link>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="px-6 mt-16 text-center text-xs text-gray-500">
        <p>Swad of Tamil © {new Date().getFullYear()}</p>
        <p className="mt-1">Authentic • Consistent • Disciplined</p>
      </footer>
    </div>
  );
}
