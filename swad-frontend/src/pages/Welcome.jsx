import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// eslint-disable-next-line no-unused-vars
import { motion } from "framer-motion";

/* ======================================================
   Welcome Page — Entry Point (Zomato/Blinkit Quality)
   Features:
   • Full screen layout
   • Big touch-friendly buttons
   • Logo + tagline
   • Choice persistence
   • Auto-redirect returning users
====================================================== */

const WELCOME_CHOICE_KEY = "swad_welcome_choice";
const WELCOME_VISITED_KEY = "swad_welcome_visited";

export default function Welcome() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);

  // Check if user has visited before
  useEffect(() => {
    const checkUserStatus = async () => {
      const hasVisited = localStorage.getItem(WELCOME_VISITED_KEY);
      const savedChoice = localStorage.getItem(WELCOME_CHOICE_KEY);

      if (hasVisited && savedChoice) {
        // Returning user - redirect to home with their preference
        navigate("/home", { state: { initialTab: savedChoice } });
        return;
      }

      // New user - show welcome page
      setIsLoading(false);
    };

    checkUserStatus();
  }, [navigate]);

  // Show loading while checking
  if (isLoading) {
    return (
      <div className="min-h-screen bg-app flex items-center justify-center">
        <div className="text-accent">Loading...</div>
      </div>
    );
  }

  const handleChoice = (choice) => {
    // Save choice and mark as visited
    localStorage.setItem(WELCOME_CHOICE_KEY, choice);
    localStorage.setItem(WELCOME_VISITED_KEY, "true");

    // Navigate to home with the choice
    navigate("/home", { state: { initialTab: choice } });
  };

  return (
    <div className="min-h-screen bg-app text-text flex flex-col">
      {/* ================= HEADER ================= */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center py-12 px-6"
      >
        <div className="max-w-md mx-auto space-y-4">
          {/* LOGO */}
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5, type: "spring" }}
            className="text-6xl mb-6"
          >
            🏪
          </motion.div>

          {/* BRAND NAME */}
          <h1 className="text-4xl font-bold font-heading text-foreground">
            Swad of Tamil
          </h1>

          {/* TAGLINE */}
          <p className="text-xl text-accent font-medium">
            Authentic Tamil Breakfast
          </p>

          {/* SUBTAGLINE */}
          <p className="text-muted text-sm max-w-sm mx-auto">
            Fresh idlis & hot sambar — made every morning in Chandigarh
          </p>
        </div>
      </motion.header>

      {/* ================= MAIN CONTENT ================= */}
      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.6 }}
        className="flex-1 flex items-center justify-center px-6"
      >
        <div className="w-full max-w-sm space-y-6">
          {/* CHOICE TITLE */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              What are you looking for?
            </h2>
            <p className="text-muted text-sm">
              Choose your preference to get started
            </p>
          </div>

          {/* CHOICE BUTTONS */}
          <div className="space-y-4">
            {/* COMBOS BUTTON */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleChoice("combos")}
              className="w-full bg-card border border-subtle rounded-2xl p-6 text-left hover:bg-surface transition-colors group"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">🍽️</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground group-hover:text-accent transition-colors">
                    Breakfast Combos
                  </h3>
                  <p className="text-muted text-sm mt-1">
                    Complete breakfast boxes with idli, sambar & more
                  </p>
                </div>
                <div className="text-2xl opacity-50 group-hover:opacity-100 transition-opacity">
                  →
                </div>
              </div>
            </motion.button>

            {/* SNACKS BUTTON */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleChoice("snacks")}
              className="w-full bg-card border border-subtle rounded-2xl p-6 text-left hover:bg-surface transition-colors group"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">🍪</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground group-hover:text-accent transition-colors">
                    Add-ons & Snacks
                  </h3>
                  <p className="text-muted text-sm mt-1">
                    Murukku, mixture, sweets & traditional snacks
                  </p>
                </div>
                <div className="text-2xl opacity-50 group-hover:opacity-100 transition-opacity">
                  →
                </div>
              </div>
            </motion.button>

            {/* SUBSCRIPTION BUTTON (FUTURE) */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleChoice("subscription")}
              className="w-full bg-card border border-subtle rounded-2xl p-6 text-left hover:bg-surface transition-colors group opacity-75"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">🔁</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground group-hover:text-accent transition-colors">
                    Daily Subscription
                  </h3>
                  <p className="text-muted text-sm mt-1">
                    Fresh breakfast delivered every morning (Coming Soon)
                  </p>
                </div>
                <div className="text-2xl opacity-50 group-hover:opacity-100 transition-opacity">
                  →
                </div>
              </div>
            </motion.button>
          </div>

          {/* SKIP OPTION */}
          <div className="text-center pt-4">
            <button
              onClick={() => handleChoice("combos")}
              className="text-muted text-sm hover:text-accent transition-colors underline"
            >
              Skip and explore everything →
            </button>
          </div>
        </div>
      </motion.main>

      {/* ================= FOOTER ================= */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.4 }}
        className="text-center py-8 px-6"
      >
        <div className="text-xs text-muted space-y-1">
          <div>📍 Sector 23C, Chandigarh</div>
          <div>🕐 Fresh batches made daily</div>
        </div>
      </motion.footer>
    </div>
  );
}