/* ======================================================
   SkeletonCard — Neutral Loading Placeholder
   Purpose: Prevent layout shift & show loading intent
====================================================== */

export default function SkeletonCard() {
  return (
    <div className="rounded-3xl border border-white/5 bg-white/2 overflow-hidden animate-pulse">

      {/* Image placeholder */}
      <div className="aspect-square bg-white/5" />

      {/* Text + action placeholder */}
      <div className="p-3 space-y-2">
        <div className="h-3 w-3/4 rounded bg-white/10" />
        <div className="h-3 w-1/2 rounded bg-white/10" />

        <div className="pt-2 flex items-center justify-between">
          <div className="h-4 w-10 rounded bg-white/10" />
          <div className="h-7 w-14 rounded-full bg-white/10" />
        </div>
      </div>
    </div>
  );
}
