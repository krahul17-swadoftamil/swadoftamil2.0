import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { usePersonalization } from "../hooks/usePersonalization";

import ComboCard from "./ComboCard";
import SnackCard from "./SnackCard";
import Carousel from "./Carousel";

/* ======================================================
   RecommendedSection — PREMIUM SHOWCASE
====================================================== */

function RecommendedSection({
  combos = [],
  snacks = [],
  onViewCombo,
  onViewSnack,
  onRequireAuth,
  isAuthenticated = false,
  currentCombo = null, // New prop for combo-aware recommendations
}) {
  const { getRecommendations } = usePersonalization();

  const hour = new Date().getHours();
  const isMorning = hour >= 4 && hour < 12;

  const recLimit = 3; // CURATED: fewer, bigger, more premium

  const chefsPickId = useMemo(() => {
    const all = [...combos, ...snacks];
    if (!all.length) return null;
    const seed = new Date().toDateString();
    return all[
      seed.split("").reduce((a, c) => a + c.charCodeAt(0), 0) % all.length
    ]?.id;
  }, [combos, snacks]);

  const { list, label } = useMemo(() => {
    // If we have a current combo, show complementary recommendations only
    if (currentCombo) {
      const complementarySnacks = snacks.filter(snack => {
        const snackName = (snack.name || '').toLowerCase();
        const comboName = (currentCombo.name || '').toLowerCase();
        
        // For idli combos, recommend sambar, chutney, and snacks
        if (comboName.includes('idli')) {
          return snackName.includes('sambar') || 
                 snackName.includes('chutney') || 
                 snackName.includes('chips') ||
                 snackName.includes('murukku');
        }
        
        // For dosa combos, recommend sambar, chutney, and snacks
        if (comboName.includes('dosa')) {
          return snackName.includes('sambar') || 
                 snackName.includes('chutney') || 
                 snackName.includes('chips') ||
                 snackName.includes('murukku');
        }
        
        // Default: show some snacks
        return snackName.includes('chips') || snackName.includes('murukku');
      });

      return {
        list: complementarySnacks.slice(0, recLimit).map(snack => ({ ...snack, type: "snack" })),
        label: `Perfect with ${currentCombo.name}`,
      };
    }

    // Show only snack recommendations
    const snackRecs = getRecommendations(snacks, "snack") || [];

    let merged = snackRecs.map((i) => ({ ...i, type: "snack" }));

    merged = merged
      .map((item) => ({
        ...item,
        _score: (item.recommendationScore || 0) * 1.4,
      }))
      .sort((a, b) => b._score - a._score)
      .slice(0, recLimit);

    return {
      list: merged,
      label: isMorning 
        ? "Picked for your breakfast today" 
        : "Curated for your evening",
    };
  }, [combos, snacks, getRecommendations, isMorning, currentCombo]);

  if (!list.length) return null;

  return (
    <section className="bg-[#0e0e0e] border-y border-white/5">
      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* HEADER */}
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-text">
              {label}
            </h2>
          </div>
        </div>

        {/* PREMIUM CAROUSEL */}
        <Carousel
          className="px-6"
          itemClassName="min-w-[280px] max-w-[300px]"
          showDots={true}
          showArrows={true}
          slidesToShow={{ mobile: 1, tablet: 2, desktop: 3 }}
          gap="gap-4"
        >
          {list.map((item) => {
            const badge =
              item.id === chefsPickId
                ? "Chef’s Pick"
                : item.is_repeat || item.order_count > 1
                ? "Ordered Again"
                : null;

            return (
              <motion.div
                key={`${item.type}-${item.id}`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.05, y: -5 }}
                transition={{ duration: 0.3 }}
                className="rounded-lg bg-gradient-to-br from-accent/20 to-accent/5 p-2 border border-accent/40 hover:border-accent/70 shadow-lg hover:shadow-accent/20 transition-all overflow-hidden"
              >
                {item.type === "combo" ? (
                  <ComboCard
                    combo={item}
                    badge={badge}
                    featured
                    onView={() => onViewCombo?.(item)}
                    onRequireAuth={onRequireAuth}
                    isAuthenticated={isAuthenticated}
                  />
                ) : (
                  <SnackCard
                    snack={item}
                    badge={badge}
                    featured
                    onView={() => onViewSnack?.(item)}
                  />
                )}
              </motion.div>
            );
          })}
        </Carousel>
      </div>
    </section>
  );
}

export default memo(RecommendedSection);
