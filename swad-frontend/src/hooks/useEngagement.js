import { useState } from 'react';

/* ======================================================
   ENGAGEMENT HOOK — Likes & Ratings
====================================================== */
export function useEngagement(itemId, itemType = 'combo') {
  const storageKey = `swad_engagement_${itemType}_${itemId}`;

  const [engagement, setEngagement] = useState(() => {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const data = JSON.parse(stored);
      return {
        likes: data.likes || 0,
        rating: data.rating || 0,
        userLiked: data.userLiked || false,
      };
    }
    return { likes: 0, rating: 0, userLiked: false };
  });

  const toggleLike = () => {
    setEngagement(prev => {
      const newLikes = prev.userLiked ? prev.likes - 1 : prev.likes + 1;
      const newUserLiked = !prev.userLiked;
      const newData = { likes: newLikes, rating: prev.rating, userLiked: newUserLiked };
      localStorage.setItem(storageKey, JSON.stringify(newData));
      return newData;
    });
  };

  const updateRating = (newRating) => {
    setEngagement(prev => {
      const newData = { ...prev, rating: newRating };
      localStorage.setItem(storageKey, JSON.stringify(newData));
      return newData;
    });
  };

  return { ...engagement, toggleLike, updateRating };
}