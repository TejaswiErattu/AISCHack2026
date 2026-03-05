import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';

const Topbar = () => {
  const { selectedRegion, isDemoMode } = useContext(AppContext);

  return (
    <nav className="h-[48px] sm:h-[56px] w-full bg-background-primary border-b border-border flex items-center justify-between px-3 sm:px-6 z-[2000] relative">
      {/* Left: Logo & Tagline */}
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="w-7 h-7 sm:w-8 sm:h-8 bg-accent-primary rounded-md flex items-center justify-center shadow-glow-teal">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A0F1E" strokeWidth="2.5" className="sm:w-5 sm:h-5">
            <path d="M3 21c3-3 7-3 10-3s7 0 10 3M5 10c2-2 5-2 7-2s5 0 7 2M8 5c1.5-1.5 3.5-1.5 5-1.5s3.5 0 5 1.5" />
          </svg>
        </div>
        <div>
          <h1 className="text-[14px] sm:text-[18px] font-bold text-text-primary leading-tight">TerraLend</h1>
          <p className="text-[9px] sm:text-[11px] text-text-muted uppercase tracking-widest font-semibold hidden sm:block">Adaptive Climate-Aware Lending</p>
        </div>
      </div>

      {/* Right: Status Badges */}
      <div className="flex items-center gap-2 sm:gap-4">
        {selectedRegion && (
          <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 bg-background-elevated rounded-badge border border-border animate-fade-in">
            <div className="w-2 h-2 rounded-full bg-accent-primary animate-pulse shadow-[0_0_8px_#00D4AA]" />
            <span className="text-[10px] sm:text-[12px] font-semibold text-text-primary uppercase tracking-wider truncate max-w-[120px] sm:max-w-none">
              LIVE: {selectedRegion.name}
            </span>
          </div>
        )}

        {isDemoMode && (
          <div className="px-2 sm:px-3 py-1 bg-accent-warning/10 border border-accent-warning/30 rounded-badge">
            <span className="text-[9px] sm:text-[10px] font-bold text-accent-warning uppercase tracking-tighter">Demo</span>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Topbar;