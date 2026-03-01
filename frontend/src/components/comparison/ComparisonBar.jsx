import React, { useState, useEffect, useContext } from 'react';
import { AppContext } from '../../context/AppContext';
import { useCountUp } from '../../hooks/useCountUp';

const ComparisonBar = () => {
  const { financialOutputs, selectedRegion } = useContext(AppContext);
  
  // Persistence logic for collapse state
  const [isExpanded, setIsExpanded] = useState(() => {
    const saved = localStorage.getItem('terra_comparison_expanded');
    return saved !== null ? JSON.parse(saved) : true;
  });

  const toggleCollapse = () => {
    const newState = !isExpanded;
    setIsExpanded(newState);
    localStorage.setItem('terra_comparison_expanded', JSON.stringify(newState));
  };

  // The non-negotiable "Awe" animation
  // Counts down from legacy rate (7.2%) to current TerraLend rate
  const terraRate = selectedRegion ? financialOutputs.interest_rate : 6.4;
  const animatedRate = useCountUp(terraRate, 800);

  const rows = [
    { label: "Updated", old: "Annually", new: "Continuously" },
    { label: "Based on", old: "Regional Average", new: "Live Climate Data" },
    { label: "Risk Model", old: "Historical Yield", new: "Microclimate Stress" },
    { label: "Farmer Visibility", old: "None", new: "Full Transparency" },
    { label: "Climate Data", old: "None", new: "5 Live Feeds" },
  ];

  return (
    <div className={`
      w-full bg-[#111827] border-t border-border transition-all duration-300 ease-in-out overflow-hidden relative
      ${isExpanded ? 'h-[160px]' : 'h-[32px]'}
    `}>
      {/* 1. COLLAPSE TOGGLE */}
      <button 
        onClick={toggleCollapse}
        className="absolute top-2 right-6 z-10 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-text-muted hover:text-accent-primary transition-colors"
      >
        <span>{isExpanded ? '▼ Hide' : '▲ Show Comparison'}</span>
      </button>

      {/* 2. MAIN CONTENT GRID */}
      <div className={`
        grid grid-cols-2 h-full transition-opacity duration-300
        ${isExpanded ? 'opacity-100' : 'opacity-0 pointer-events-none'}
      `}>
        
        {/* LEFT COLUMN: OLD SYSTEM (Muted/Red Tint) */}
        <div className="bg-accent-danger/[0.03] border-r border-border/30 px-8 py-4 flex flex-col justify-center">
          <h4 className="text-[11px] uppercase text-text-muted font-medium mb-3 tracking-widest">
            Old System
          </h4>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[14px] text-text-muted">Rate:</span>
            <span className="text-[18px] font-mono text-text-muted line-through opacity-60">7.2%</span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {rows.slice(0, 4).map(row => (
              <div key={row.label} className="flex justify-between text-[11px]">
                <span className="text-text-muted/50">{row.label}:</span>
                <span className="text-text-muted/80">{row.old}</span>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: TERRALEND (Vibrant/Teal Tint) */}
        <div className="bg-accent-primary/[0.03] px-8 py-4 flex flex-col justify-center">
          <h4 className="text-[11px] uppercase text-accent-primary font-bold mb-3 tracking-widest">
            TerraLend
          </h4>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[14px] text-text-secondary">Rate:</span>
            <span className="text-[20px] font-mono font-bold text-accent-primary shadow-glow-teal px-2 bg-accent-primary/5 rounded">
              {animatedRate.toFixed(1)}%
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {rows.slice(0, 4).map(row => (
              <div key={row.label} className="flex justify-between text-[11px]">
                <span className="text-text-muted">{row.label}:</span>
                <span className="text-text-primary font-medium">{row.new}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComparisonBar;