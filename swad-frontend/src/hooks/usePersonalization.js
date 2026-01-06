import { useState, useEffect, useMemo } from 'react';

/* ======================================================
   PERSONALIZATION HOOK — Smart Recommendations
====================================================== */

const VIEWED_KEY = 'swad_viewed_items';
const CLICKS_KEY = 'swad_session_clicks';
const FAVORITES_KEY = 'swad_favorites';

export function usePersonalization() {
  // Track viewed items (persistent across sessions)
  const [viewedItems, setViewedItems] = useState(() => {
    const stored = localStorage.getItem(VIEWED_KEY);
    return stored ? JSON.parse(stored) : [];
  });

  // Track clicks in current session (resets on page refresh)
  const [sessionClicks, setSessionClicks] = useState(() => {
    const stored = sessionStorage.getItem(CLICKS_KEY);
    return stored ? JSON.parse(stored) : {};
  });

  // Track favorite combos (derived from engagement data)
  const [favorites, setFavorites] = useState(() => {
    const stored = localStorage.getItem(FAVORITES_KEY);
    return stored ? JSON.parse(stored) : [];
  });

  // Save viewed items to localStorage
  useEffect(() => {
    localStorage.setItem(VIEWED_KEY, JSON.stringify(viewedItems));
  }, [viewedItems]);

  // Save session clicks to sessionStorage
  useEffect(() => {
    sessionStorage.setItem(CLICKS_KEY, JSON.stringify(sessionClicks));
  }, [sessionClicks]);

  // Save favorites to localStorage
  useEffect(() => {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  }, [favorites]);

  // Track when an item is viewed
  const trackView = (itemId, itemType = 'combo') => {
    const itemKey = `${itemType}_${itemId}`;
    setViewedItems(prev => {
      const filtered = prev.filter(item => item.key !== itemKey);
      return [{ key: itemKey, id: itemId, type: itemType, timestamp: Date.now() }, ...filtered].slice(0, 20); // Keep last 20
    });
  };

  // Track when an item is clicked (added to cart)
  const trackClick = (itemId, itemType = 'combo') => {
    const itemKey = `${itemType}_${itemId}`;
    setSessionClicks(prev => ({
      ...prev,
      [itemKey]: (prev[itemKey] || 0) + 1
    }));
  };

  // Add/remove favorite
  const toggleFavorite = (itemId, itemType = 'combo') => {
    const itemKey = `${itemType}_${itemId}`;
    setFavorites(prev => {
      const isFavorite = prev.some(item => item.key === itemKey);
      if (isFavorite) {
        return prev.filter(item => item.key !== itemKey);
      } else {
        return [...prev, { key: itemKey, id: itemId, type: itemType, timestamp: Date.now() }];
      }
    });
  };

  // Check if item is favorite
  const isFavorite = (itemId, itemType = 'combo') => {
    const itemKey = `${itemType}_${itemId}`;
    return favorites.some(item => item.key === itemKey);
  };

  // Get recommendations based on user behavior
  const getRecommendations = (allItems, currentItemType = 'combo') => {
    if (!allItems || allItems.length === 0) return [];

    // Score items based on multiple factors
    const scoredItems = allItems.map(item => {
      const itemKey = `${currentItemType}_${item.id}`;
      let score = 0;

      // Factor 1: Recently viewed (higher weight for recent views)
      const viewedItem = viewedItems.find(v => v.key === itemKey);
      if (viewedItem) {
        const daysSinceViewed = (Date.now() - viewedItem.timestamp) / (1000 * 60 * 60 * 24);
        score += Math.max(0, 10 - daysSinceViewed); // Decay over 10 days
      }

      // Factor 2: Session clicks (most clicked items)
      const clickCount = sessionClicks[itemKey] || 0;
      score += clickCount * 5; // Each click adds 5 points

      // Factor 3: Favorites (highest weight)
      if (isFavorite(item.id, currentItemType)) {
        score += 20;
      }

      // Factor 4: Item popularity (likes from engagement)
      const engagementKey = `swad_engagement_${currentItemType}_${item.id}`;
      const engagementData = localStorage.getItem(engagementKey);
      if (engagementData) {
        const { likes = 0 } = JSON.parse(engagementData);
        score += likes * 0.5; // Likes add 0.5 points each
      }

      // Factor 5: Chef's special or featured items
      if (item.is_featured || item.is_best_seller) {
        score += 3;
      }

      return { ...item, recommendationScore: score };
    });

    // Sort by score (highest first) and filter out items with very low scores
    return scoredItems
      .filter(item => item.recommendationScore > 0)
      .sort((a, b) => b.recommendationScore - a.recommendationScore)
      .slice(0, 6); // Return top 6 recommendations
  };

  // Get favorite items
  const getFavorites = () => {
    return favorites.map(fav => ({
      id: fav.id,
      type: fav.type,
      timestamp: fav.timestamp
    }));
  };

  // Clear session data (useful for testing)
  const clearSessionData = () => {
    setSessionClicks({});
    sessionStorage.removeItem(CLICKS_KEY);
  };

  return {
    viewedItems,
    sessionClicks,
    favorites: getFavorites(),
    trackView,
    trackClick,
    toggleFavorite,
    isFavorite,
    getRecommendations,
    clearSessionData
  };
}