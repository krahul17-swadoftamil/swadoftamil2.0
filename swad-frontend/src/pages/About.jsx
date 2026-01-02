import { motion, useReducedMotion } from "framer-motion";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

/* ======================================================
   ABOUT — SWAD OF TAMIL (PREMIUM + TRUST + CTA)
====================================================== */

export default function About() {
  const reduceMotion = useReducedMotion();
  const [showCTA, setShowCTA] = useState(false);

  /* ================= SCROLL CTA ================= */
  useEffect(() => {
    const onScroll = () => {
      setShowCTA(window.scrollY > 500);
    };
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const fadeUp = {
    hidden: { opacity: 0, y: reduceMotion ? 0 : 28 },
    visible: {
      opacity: 1,
      y: 0,
      transition: reduceMotion
        ? { duration: 0 }
        : { duration: 0.7, ease: "easeOut" },
    },
  };

  const glow =
    "transition-all duration-300 hover:shadow-[0_0_40px_rgba(255,170,70,0.35)] hover:-translate-y-1";

  return (
    <>
      {/* ================= SEO ================= */}
      <title>About Swad of Tamil | Authentic Tamil Breakfast</title>
      <meta
        name="description"
        content="Authentic Tamil breakfast rooted in Ayurveda-inspired food wisdom. Fresh idli, sambar, chutneys — prepared daily in Chandigarh."
      />

      <div className="min-h-screen bg-gradient-to-br from-neutral-950 via-black to-neutral-900 text-white">

        {/* ================= HERO ================= */}
        <section className="relative px-6 pt-28 pb-24 text-center overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,186,73,0.15),transparent_65%)]" />

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fadeUp}
            className="relative max-w-3xl mx-auto"
          >
            <p className="uppercase tracking-[0.35em] text-xs text-amber-400 mb-4">
              Swad of Tamil
            </p>

            <h1 className="text-4xl md:text-5xl font-semibold leading-tight">
              Ancient Tamil food,
              <br />
              <span className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                served with modern discipline
              </span>
            </h1>

            <p className="mt-6 text-sm md:text-base text-neutral-400 leading-relaxed">
              Calm, nourishing breakfast rooted in Tamil tradition —  
              prepared daily, without shortcuts or noise.
            </p>

            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <Link
                to="/"
                className="px-8 py-3 rounded-full bg-accent text-black font-semibold"
              >
                Order Breakfast →
              </Link>
              <Link
                to="/snacks"
                className="px-8 py-3 rounded-full bg-white/10 text-white"
              >
                Explore Snacks
              </Link>
            </div>
          </motion.div>
        </section>

        {/* ================= MINI COMBOS ================= */}
        <section className="px-6">
          <div className="max-w-6xl mx-auto grid sm:grid-cols-3 gap-6">
            {[
              ["🍽️ Solo Idli Box", "Light, calming start"],
              ["👫 Duet Idli Box", "Perfectly balanced for two"],
              ["👨‍👩‍👧‍👦 Family Box", "Shared comfort"],
            ].map(([title, desc]) => (
              <motion.div
                key={title}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className={`rounded-2xl p-6 bg-white/5 border border-white/10 ${glow}`}
              >
                <h3 className="font-medium mb-2">{title}</h3>
                <p className="text-sm text-neutral-400 mb-4">{desc}</p>
                <Link to="/" className="text-sm text-accent underline">
                  View combo →
                </Link>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ================= AYURVEDA PHILOSOPHY ================= */}
        <section className="px-6 mt-28 text-center">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="max-w-3xl mx-auto"
          >
            <h2 className="text-2xl font-semibold mb-6">
              Food wisdom, not food trends
            </h2>
            <p className="text-sm text-neutral-400 leading-relaxed">
              Tamil breakfast follows principles similar to Ayurveda —
              light in the morning, fermented for digestion, warm for balance.
              Idli is <strong>laghu</strong> (light), sambar is grounding,
              chutneys complete the taste and nourishment.
            </p>

            <div className="mt-8 flex flex-wrap justify-center gap-3 text-xs">
              {[
                "🌿 Easy to digest",
                "🔥 Warm & grounding",
                "⚖️ Balanced taste",
              ].map((t) => (
                <span
                  key={t}
                  className="px-4 py-2 rounded-full border border-white/10 bg-white/5"
                >
                  {t}
                </span>
              ))}
            </div>
          </motion.div>
        </section>

        {/* ================= TESTIMONIALS ================= */}
        <section className="px-6 mt-28">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl font-semibold text-center mb-12">
              What customers say
            </h2>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                ["“Feels like home food.”", "— PGI Staff"],
                ["“Light breakfast, no heaviness.”", "— Morning Walker"],
                ["“Consistent taste every day.”", "— Regular Customer"],
              ].map(([quote, author]) => (
                <motion.div
                  key={author}
                  variants={fadeUp}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className={`rounded-2xl p-6 bg-white/5 border border-white/10 ${glow}`}
                >
                  <p className="text-sm italic text-neutral-300 mb-3">
                    {quote}
                  </p>
                  <p className="text-xs text-neutral-400">{author}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ================= LOCATION & TIMINGS ================= */}
        <section className="px-6 mt-28 text-center">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">
              Where & when to find us
            </h2>

            <p className="text-sm text-neutral-400 mb-4">
              📍 Sector 23C, Chandigarh  
              <br />
              ⏰ Morning breakfast hours: <strong>6:30 AM – 11:30 AM</strong>
            </p>

            <p className="text-xs text-neutral-500">
              Limited batches · Fresh preparation · Morning only
            </p>
          </div>
        </section>

        {/* ================= FINAL CTA ================= */}
        <section className="px-6 mt-32 pb-24 text-center">
          <Link
            to="/"
            className="inline-block px-10 py-4 rounded-full bg-accent text-black font-semibold text-lg"
          >
            Experience Swad of Tamil →
          </Link>
        </section>

        {/* ================= FOOTER ================= */}
        <footer className="pb-10 text-center text-xs text-neutral-500">
          <p>© {new Date().getFullYear()} Swad of Tamil</p>
          <p className="mt-1">Authentic • Hygienic • Disciplined</p>
        </footer>

        {/* ================= SCROLL CTA ================= */}
        {showCTA && (
          <div className="fixed bottom-4 inset-x-0 z-50 flex justify-center">
            <Link
              to="/"
              className="px-6 py-3 rounded-full bg-accent text-black font-semibold shadow-lg"
            >
              Order Breakfast →
            </Link>
          </div>
        )}
      </div>
    </>
  );
}
