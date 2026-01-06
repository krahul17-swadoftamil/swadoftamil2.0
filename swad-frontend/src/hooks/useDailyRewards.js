import { useState, useEffect } from 'react';

/* ======================================================
   DAILY CHECK-IN & REWARDS HOOK
====================================================== */

const CHECKIN_KEY = 'swad_daily_checkins';
const STREAK_KEY = 'swad_current_streak';
const LAST_CHECKIN_KEY = 'swad_last_checkin';

export function useDailyRewards() {
  const [checkIns, setCheckIns] = useState(() => {
    const stored = localStorage.getItem(CHECKIN_KEY);
    return stored ? JSON.parse(stored) : [];
  });

  const [currentStreak, setCurrentStreak] = useState(() => {
    const stored = localStorage.getItem(STREAK_KEY);
    return stored ? parseInt(stored) : 0;
  });

  const [lastCheckIn, setLastCheckIn] = useState(() => {
    const stored = localStorage.getItem(LAST_CHECKIN_KEY);
    return stored ? new Date(stored) : null;
  });

  // Check if user can check in today
  const canCheckInToday = () => {
    if (!lastCheckIn) return true;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const lastCheckInDate = new Date(lastCheckIn);
    lastCheckInDate.setHours(0, 0, 0, 0);

    const diffTime = today.getTime() - lastCheckInDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    return diffDays >= 1; // Can check in if it's been at least 1 day
  };

  // Check if streak is maintained (checked in yesterday or today)
  const isStreakMaintained = () => {
    if (!lastCheckIn) return false;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const lastCheckInDate = new Date(lastCheckIn);
    lastCheckInDate.setHours(0, 0, 0, 0);

    const diffTime = today.getTime() - lastCheckInDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    return diffDays <= 1; // Streak maintained if checked in today or yesterday
  };

  // Perform daily check-in
  const checkIn = () => {
    if (!canCheckInToday()) return false;

    const today = new Date();
    const todayString = today.toDateString();

    // Update check-ins
    const newCheckIns = [...checkIns, todayString];
    setCheckIns(newCheckIns);
    localStorage.setItem(CHECKIN_KEY, JSON.stringify(newCheckIns));

    // Update streak
    let newStreak;
    if (isStreakMaintained()) {
      newStreak = currentStreak + 1;
    } else {
      newStreak = 1; // Reset streak if broken
    }
    setCurrentStreak(newStreak);
    localStorage.setItem(STREAK_KEY, newStreak.toString());

    // Update last check-in
    setLastCheckIn(today);
    localStorage.setItem(LAST_CHECKIN_KEY, today.toISOString());

    return true;
  };

  // Get current reward based on streak
  const getCurrentReward = () => {
    if (currentStreak >= 7) return { discount: 10, message: '10% off for 7 days in a row! 🎉' };
    if (currentStreak >= 5) return { discount: 5, message: '5% off for your 5th breakfast in a row! ⭐' };
    if (currentStreak >= 3) return { discount: 3, message: '3% off for 3 days in a row! 🔥' };
    return null;
  };

  // Get streak progress info
  const getStreakInfo = () => {
    const nextMilestone = currentStreak >= 7 ? null :
                          currentStreak >= 5 ? 7 :
                          currentStreak >= 3 ? 5 : 3;

    return {
      current: currentStreak,
      nextMilestone,
      progress: nextMilestone ? (currentStreak / nextMilestone) * 100 : 100,
      canCheckIn: canCheckInToday(),
      reward: getCurrentReward()
    };
  };

  // Reset data (for testing)
  const resetData = () => {
    setCheckIns([]);
    setCurrentStreak(0);
    setLastCheckIn(null);
    localStorage.removeItem(CHECKIN_KEY);
    localStorage.removeItem(STREAK_KEY);
    localStorage.removeItem(LAST_CHECKIN_KEY);
  };

  return {
    checkIn,
    getStreakInfo,
    resetData,
    checkIns,
    currentStreak,
    lastCheckIn
  };
}