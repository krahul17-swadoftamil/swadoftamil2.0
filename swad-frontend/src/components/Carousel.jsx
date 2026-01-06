import { useCallback, useEffect, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";

/* ======================================================
   Premium Carousel Component
====================================================== */

function Carousel({
  children,
  className = "",
  itemClassName = "",
  showDots = true,
  showArrows = true,
  slidesToShow = { mobile: 1, tablet: 2, desktop: 3 },
  gap = "gap-6",
}) {
  const [emblaRef, emblaApi] = useEmblaCarousel({
    align: "start",
    slidesToScroll: 1,
    containScroll: "trimSnaps",
    dragFree: false,
    skipSnaps: false,
  });

  const [prevBtnDisabled, setPrevBtnDisabled] = useState(true);
  const [nextBtnDisabled, setNextBtnDisabled] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [scrollSnaps, setScrollSnaps] = useState([]);

  const scrollPrev = useCallback(() => {
    if (emblaApi) emblaApi.scrollPrev();
  }, [emblaApi]);

  const scrollNext = useCallback(() => {
    if (emblaApi) emblaApi.scrollNext();
  }, [emblaApi]);

  const scrollTo = useCallback(
    (index) => {
      if (emblaApi) emblaApi.scrollTo(index);
    },
    [emblaApi]
  );

  const onInit = useCallback((emblaApi) => {
    setScrollSnaps(emblaApi.scrollSnapList());
  }, []);

  const onSelect = useCallback((emblaApi) => {
    setSelectedIndex(emblaApi.selectedScrollSnap());
    setPrevBtnDisabled(!emblaApi.canScrollPrev());
    setNextBtnDisabled(!emblaApi.canScrollNext());
  }, []);

  useEffect(() => {
    if (!emblaApi) return;

    onInit(emblaApi);
    onSelect(emblaApi);
    emblaApi.on("reInit", onInit);
    emblaApi.on("reInit", onSelect);
    emblaApi.on("select", onSelect);
  }, [emblaApi, onInit, onSelect]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        scrollPrev();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        scrollNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [scrollPrev, scrollNext]);

  return (
    <div className={`relative ${className}`}>
      {/* Carousel Container */}
      <div className="overflow-hidden" ref={emblaRef}>
        <div className={`flex ${gap}`}>
          {children.map((child, index) => (
            <motion.div
              key={index}
              className={`flex-shrink-0 transition-transform duration-300 ${itemClassName}`}
              animate={{
                scale: selectedIndex === index ? 1.05 : 1,
              }}
              whileHover={{ scale: selectedIndex === index ? 1.08 : 1.02 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            >
              {child}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Navigation Arrows */}
      {showArrows && (
        <>
          <AnimatePresence>
            {!prevBtnDisabled && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                onClick={scrollPrev}
                className="
                  absolute left-2 top-1/2 -translate-y-1/2
                  bg-black/60 backdrop-blur-sm text-white
                  rounded-full p-3 shadow-lg
                  hover:bg-black/80 transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-accent/40
                  z-10
                "
                aria-label="Previous"
              >
                <ChevronLeft className="w-5 h-5" />
              </motion.button>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {!nextBtnDisabled && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                onClick={scrollNext}
                className="
                  absolute right-2 top-1/2 -translate-y-1/2
                  bg-black/60 backdrop-blur-sm text-white
                  rounded-full p-3 shadow-lg
                  hover:bg-black/80 transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-accent/40
                  z-10
                "
                aria-label="Next"
              >
                <ChevronRight className="w-5 h-5" />
              </motion.button>
            )}
          </AnimatePresence>
        </>
      )}

      {/* Dots Indicator */}
      {showDots && scrollSnaps.length > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          {scrollSnaps.map((_, index) => (
            <motion.button
              key={index}
              onClick={() => scrollTo(index)}
              className={`
                w-2 h-2 rounded-full transition-all duration-300
                ${index === selectedIndex
                  ? "bg-accent scale-125"
                  : "bg-white/30 hover:bg-white/50"
                }
              `}
              whileHover={{ scale: 1.2 }}
              whileTap={{ scale: 0.9 }}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default Carousel;