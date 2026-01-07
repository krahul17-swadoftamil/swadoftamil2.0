import { motion } from "framer-motion";

/* ======================================================
   ContextualSignIn — Converts Intent → Login
====================================================== */

function ContextualSignIn({ onContinue, onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        className="bg-card border border-subtle rounded-2xl p-6 max-w-sm w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* EMOJI + MESSAGE */}
        <div className="text-center space-y-4">
          <div className="text-4xl">👋</div>
          
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-foreground">
              Save your breakfast preference?
            </h3>
            <p className="text-sm text-muted">
              Sign in to remember your favorites and reorder easily
            </p>
          </div>

          {/* CONTINUE BUTTON */}
          <button
            onClick={onContinue}
            className="w-full py-3 px-4 rounded-xl text-sm font-semibold bg-accent text-black hover:bg-accent/90 transition-colors"
          >
            Continue with Google
          </button>

          {/* CLOSE BUTTON */}
          <button
            onClick={onClose}
            className="w-full py-2 px-4 text-sm text-muted hover:text-foreground transition-colors"
          >
            Maybe later
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default ContextualSignIn;