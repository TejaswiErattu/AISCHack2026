import React from 'react';

// Shared Shimmer Style
const shimmerClass = "animate-shimmer bg-[length:200%_100%] bg-gradient-to-r from-[#1A2235] via-[#1E3A5F] to-[#1A2235]";

export const SkeletonCard = () => (
  <div className={`h-[110px] w-full rounded-card border border-border ${shimmerClass}`} />
);

export const SkeletonGauge = () => (
  <div className={`w-[200px] h-[110px] rounded-[100px_100px_0_0] ${shimmerClass} opacity-50`} />
);

export const SkeletonNarrative = () => (
  <div className="space-y-3 p-5 rounded-card border border-border bg-background-secondary/50">
    <div className={`h-3 w-1/3 rounded ${shimmerClass}`} />
    <div className={`h-4 w-full rounded ${shimmerClass}`} />
    <div className={`h-4 w-5/6 rounded ${shimmerClass}`} />
    <div className={`h-4 w-4/6 rounded ${shimmerClass}`} />
  </div>
);

export const SkeletonChart = () => (
  <div className={`h-[160px] w-full rounded-card border border-border ${shimmerClass}`} />
);

export const SkeletonIndexRow = () => (
  <div className="grid grid-cols-5 gap-2 w-full">
    {[...Array(5)].map((_, i) => (
      <div key={i} className={`h-[74px] rounded-md border border-border ${shimmerClass}`} />
    ))}
  </div>
);

export const SkeletonRateCard = () => (
  <div className={`h-[180px] w-full rounded-card border border-border ${shimmerClass}`} />
);