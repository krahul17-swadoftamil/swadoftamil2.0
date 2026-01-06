import { memo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDailyRewards } from "../hooks/useDailyRewards";
import confetti from 'canvas-confetti';

/* ======================================================
   DAILY REWARDS COMPONENT
====================================================== */

function DailyRewards() {
  const { checkIn, getStreakInfo } = useDailyRewards();
  const [showReward, setShowReward] = useState(false);
  const [lastReward, setLastReward] = useState(null);

  const streakInfo = getStreakInfo();

  const handleCheckIn = () => {
    const success = checkIn();
    if (success) {
      const updatedInfo = getStreakInfo();
      if (updatedInfo.reward) {
        setLastReward(updatedInfo.reward);
        setShowReward(true);

        // Trigger confetti
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#ffaa00', '#ff6b35', '#f7931e', '#ffd23f', '#4ade80'],
          gravity: 0.8,
          drift: 0.1
        });

        // Hide reward message after 3 seconds
        setTimeout(() => setShowReward(false), 3000);
      }
    }
  };

  const getStreakEmoji = (streak) => {
    if (streak >= 7) return '🔥🔥🔥';
    if (streak >= 5) return '⭐⭐⭐';
    if (streak >= 3) return '🔥🔥';
    return '🌟';
  };

  return (
    <div className="bg-gradient-to-r from-orange-500/10 to-yellow-500/10 border border-orange-200/20 rounded-2xl p-4 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">📅</span>
          <span className="font-semibold text-text">Daily Check-in</span>
        </div>
        <div className="text-right">
          <div className="text-sm font-medium text-text">
            {streakInfo.current} day{streakInfo.current !== 1 ? 's' : ''}
          </div>
          <div className="text-xs text-muted">streak</div>
        </div>
      </div>

      {/* Progress Bar */}
      {streakInfo.nextMilestone && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-muted mb-1">
            <span>Progress to next reward</span>
            <span>{streakInfo.current}/{streakInfo.nextMilestone}</span>
          </div>
          <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${streakInfo.progress}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-orange-400 to-yellow-400 rounded-full"
            />
          </div>
        </div>
      )}

      {/* Check-in Button */}
      <button
        onClick={handleCheckIn}
        disabled={!streakInfo.canCheckIn}
        className={`
          w-full py-2.5 rounded-xl font-semibold transition-all duration-200
          ${streakInfo.canCheckIn
            ? 'bg-accent text-black hover:bg-accent/90 active:scale-95 shadow-lg'
            : 'bg-subtle text-muted cursor-not-allowed'
          }
        `}
      >
        {streakInfo.canCheckIn ? 'Check In Today! 🎯' : 'Already checked in today'}
      </button>

      {/* Current Reward Display */}
      {streakInfo.reward && !showReward && (
        <div className="mt-3 text-center">
          <div className="text-sm font-medium text-accent">
            {getStreakEmoji(streakInfo.current)} {streakInfo.reward.message}
          </div>
        </div>
      )}

      {/* Reward Celebration */}
      <AnimatePresence>
        {showReward && lastReward && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -20 }}
            className="mt-3 text-center bg-accent/10 border border-accent/20 rounded-xl p-3"
          >
            <motion.div
              animate={{ rotate: [0, -10, 10, -10, 0] }}
              transition={{ duration: 0.5, repeat: 3 }}
              className="text-2xl mb-1"
            >
              🎉
            </motion.div>
            <div className="font-semibold text-accent text-sm">
              {lastReward.message}
            </div>
            <div className="text-xs text-muted mt-1">
              Reward unlocked! Use it on your next order.
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default memo(DailyRewards);