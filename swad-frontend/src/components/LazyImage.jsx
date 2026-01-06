import { useState } from 'react';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import 'react-lazy-load-image-component/src/effects/blur.css';

/* ======================================================
   LazyImage — Progressive Image Loading Pipeline
   • API-first: Uses image_url/thumbnail_url from backend
   • Lazy loading: Only loads when in viewport
   • Blur-up effect: Smooth transition from placeholder to image
   • Skeleton loading: Animated gradient while loading
   • Error handling: Graceful fallback for broken images
====================================================== */

export default function LazyImage({
  src,
  alt,
  className = "",
  placeholderSrc,
  showSkeleton = true,
  ...props
}) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // Create a tiny blurred placeholder if none provided
  const blurPlaceholder = placeholderSrc || createBlurPlaceholder();

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  return (
    <div className={`relative ${className}`}>
      {/* SKELETON LOADER */}
      {showSkeleton && isLoading && !hasError && (
        <div className="absolute inset-0 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-pulse rounded-lg">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer rounded-lg" 
               style={{
                 background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                 backgroundSize: '200% 100%',
                 animation: 'shimmer 1.5s infinite'
               }} />
        </div>
      )}

      {/* ERROR STATE */}
      {hasError && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center rounded-lg">
          <div className="text-gray-400 text-sm">Image unavailable</div>
        </div>
      )}

      {/* LAZY LOADED IMAGE */}
      <LazyLoadImage
        src={src}
        alt={alt}
        className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
        placeholderSrc={blurPlaceholder}
        effect="blur"
        threshold={100}
        delayMethod="throttle"
        delayTime={300}
        onLoad={handleLoad}
        onError={handleError}
        {...props}
      />
    </div>
  );
}

// Create a simple blur placeholder (1x1 pixel blurred image)
function createBlurPlaceholder() {
  // Return a data URL for a tiny blurred placeholder
  // This creates a very small blurred image as a data URL
  return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8ZGVmcz4KICAgIDxmaWx0ZXIgaWQ9ImJsdXIiIHg9IjAiIHk9IjAiIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPgogICAgICA8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIxIi8+CiAgICA8L2ZpbHRlcj4KICA8L2RlZnM+CiAgPHJlY3Qgd2lkdGg9IjEwIiBoZWlnaHQ9IjEwIiBmaWxsPSIjRjNGNEY2IiBmaWx0ZXI9InVybCgjYmx1cikiLz4KPC9zdmc+";
}