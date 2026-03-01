import React from 'react';

/**
 * StressBar Component
 * Renders a horizontal progress bar for climate risk factors.
 *
 */
const StressBar = ({ label, value, color }) => {
  return (
    <div className="w-full space-y-1.5">
      <div className="flex justify-between items-center text-[11px] font-medium">
        <span className="text-text-secondary uppercase tracking-wider">{label}</span>
        <span className="font-mono text-text-primary">{value}%</span>
      </div>
      
      <div className="h-2 w-full bg-background-secondary rounded-full overflow-hidden border border-border/30">
        <div 
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ 
            width: `${value}%`, 
            backgroundColor: color,
            boxShadow: `0 0 8px ${color}44` 
          }}
        />
      </div>
    </div>
  );
};

export default StressBar;