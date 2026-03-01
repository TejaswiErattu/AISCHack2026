import React from 'react';

/**
 * DeltaIndicator Component
 * Renders a colored trend indicator (arrow + percentage) for financial metrics.
 *
 */
const DeltaIndicator = ({ 
  value = 0, 
  label = "vs baseline", 
  reverseColor = false 
}) => {
  if (value === 0) return null;

  const isPositive = value > 0;
  
  // Logic: Generally, an increase in rate/stress is 'bad' (Red), 
  // but for some metrics like 'Repayment Flex', up is 'good' (Green).
  const isGood = reverseColor ? isPositive : !isPositive;
  
  const colorClass = isGood ? 'text-accent-positive' : 'text-accent-danger';
  const icon = isPositive ? '↑' : '↓';

  return (
    <div className={`flex items-center gap-1 font-mono text-[11px] font-semibold ${colorClass}`}>
      <span>{icon}</span>
      <span>{Math.abs(value).toFixed(1)}%</span>
      {label && <span className="text-text-muted ml-0.5 font-sans lowercase">{label}</span>}
    </div>
  );
};

export default DeltaIndicator;