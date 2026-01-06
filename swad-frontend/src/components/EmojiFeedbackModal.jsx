import { memo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ======================================================
   EMOJI FEEDBACK MODAL
====================================================== */

function EmojiFeedbackModal({ isOpen, onClose, onSubmit }) {
  const [selectedEmoji, setSelectedEmoji] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const emojis = [
    { emoji: '😋', label: 'Delicious!', value: 'happy' },
    { emoji: '😐', label: 'Okay', value: 'neutral' },
    { emoji: '😞', label: 'Not great', value: 'sad' }
  ];

  const handleSubmit = () => {
    if (selectedEmoji && !submitted) {
      setSubmitted(true);
      onSubmit(selectedEmoji);

      // Close modal after a short delay
      setTimeout(() => {
        onClose();
        setSelectedEmoji(null);
        setSubmitted(false);
      }, 1500);
    }
  };

  const handleClose = () => {
    if (!submitted) {
      onClose();
      setSelectedEmoji(null);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-card border border-subtle rounded-3xl p-6 max-w-sm w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="text-center mb-6">
              <h3 className="text-lg font-semibold text-text mb-2">
                How was your breakfast today?
              </h3>
              <p className="text-sm text-muted">
                Your feedback helps us improve! 🌟
              </p>
            </div>

            {/* Emoji Options */}
            <div className="flex justify-center gap-4 mb-6">
              {emojis.map((item, index) => (
                <motion.button
                  key={item.value}
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{
                    delay: index * 0.1,
                    type: "spring",
                    damping: 20,
                    stiffness: 300
                  }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSelectedEmoji(item)}
                  className={`
                    w-16 h-16 rounded-full border-2 transition-all duration-200 flex flex-col items-center justify-center
                    ${selectedEmoji?.value === item.value
                      ? 'border-accent bg-accent/10 scale-110'
                      : 'border-subtle hover:border-accent/50'
                    }
                  `}
                  disabled={submitted}
                >
                  <span className="text-2xl mb-1">{item.emoji}</span>
                  <span className="text-xs text-muted">{item.label}</span>
                </motion.button>
              ))}
            </div>

            {/* Submit Button */}
            <AnimatePresence mode="wait">
              {submitted ? (
                <motion.div
                  key="submitted"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="text-center py-4"
                >
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.5, repeat: 2 }}
                    className="text-3xl mb-2"
                  >
                    {selectedEmoji?.emoji}
                  </motion.div>
                  <p className="text-sm text-accent font-medium">
                    Thanks for your feedback! 🙏
                  </p>
                </motion.div>
              ) : (
                <motion.button
                  key="submit"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  onClick={handleSubmit}
                  disabled={!selectedEmoji}
                  className={`
                    w-full py-3 rounded-xl font-semibold transition-all duration-200
                    ${selectedEmoji
                      ? 'bg-accent text-black hover:bg-accent/90 active:scale-95'
                      : 'bg-subtle text-muted cursor-not-allowed'
                    }
                  `}
                >
                  {selectedEmoji ? 'Submit Feedback' : 'Select an emoji'}
                </motion.button>
              )}
            </AnimatePresence>

            {/* Close button */}
            {!submitted && (
              <button
                onClick={handleClose}
                className="absolute top-3 right-3 text-muted hover:text-text transition-colors"
              >
                ✕
              </button>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default memo(EmojiFeedbackModal);