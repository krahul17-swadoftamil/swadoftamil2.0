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
    const comboRecs = getRecommendations(combos, "combo") || [];
    const snackRecs = getRecommendations(snacks, "snack") || [];

    let merged = [
      ...comboRecs.map((i) => ({ ...i, type: "combo" })),
      ...snackRecs.map((i) => ({ ...i, type: "snack" })),
    ];

    merged = merged
      .map((item) => ({
        ...item,
        _score:
          (item.recommendationScore || 0) *
          (isMorning && item.type === "combo"
            ? 1.4
            : !isMorning && item.type === "snack"
            ? 1.4
            : 1),
      }))
      .sort((a, b) => b._score - a._score)
      .slice(0, recLimit);

    return {
      list: merged,
      label: isMorning 
        ? "Picked for your breakfast today" 
        : "Curated for your evening",
    };
  }, [combos, snacks, getRecommendations, isMorning]);

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
          itemClassName="min-w-[420px] max-w-[440px]"
          showDots={true}
          showArrows={true}
          slidesToShow={{ mobile: 1, tablet: 1, desktop: 1 }}
          gap="gap-6"
        >
          {list.map((item) => {
            const badge =
              item.id === chefsPickId
                ? "Chef’s Pick"
                : item.is_repeat || item.order_count > 1
                ? "Ordered Again"
                : null;

            return item.type === "combo" ? (
              <ComboCard
                key={`${item.type}-${item.id}`}
                combo={item}
                badge={badge}
                featured
                onView={() => onViewCombo?.(item)}
              />
            ) : (
              <SnackCard
                key={`${item.type}-${item.id}`}
                snack={item}
                badge={badge}
                featured
                onView={() => onViewSnack?.(item)}
              />
            );
          })}
        </Carousel>
      </div>
    </section>
  );
}

export default memo(RecommendedSection);
