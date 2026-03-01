import React from 'react';
import { useCountUp } from '../../hooks/useCountUp';

const FinancialCard = ({ label, value, unit, prefix = '', delta, variant }) => {
  const displayValue = useCountUp(value);
  const isUp = delta > 0;

  const borderClass = variant === 'ai-floor' ? 'border-accent-primary' : 
                      variant === 'ai-ceiling' ? 'border-accent-warning' : 'border-border';

  return (
    <div className={`bg-background-card border ${borderClass} rounded-card p-4 transition-all hover:bg-background-elevated`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{label}</span>
        {(variant === 'ai-floor' || variant === 'ai-ceiling') && (
          <span className="text-[8px] bg-background-elevated px-1.5 py-0.5 rounded border border-border text-text-secondary">AI</span>
        )}
      </div>
      
      <div className="flex items-baseline gap-1">
        <span className="font-mono text-[24px] font-bold text-text-primary">
          {prefix}{displayValue.toFixed(unit === '%' ? 1 : 0)}
        </span>
        <span className="font-mono text-[14px] text-text-secondary">{unit}</span>
      </div>

      {delta !== undefined && (
        <div className={`flex items-center gap-1 text-[11px] font-mono font-semibold mt-1 ${isUp ? 'text-accent-danger' : 'text-accent-positive'}`}>
          <span>{isUp ? '↑' : '↓'}</span>
          <span>{Math.abs(delta).toFixed(1)}% vs baseline</span>
        </div>
      )}

      {/* Mini Stress Bar */}
      <div className="mt-3 h-[4px] w-full bg-background-secondary rounded-full overflow-hidden">
        <div 
          className="h-full bg-accent-primary rounded-full transition-all duration-1000"
          style={{ width: `${Math.min(value * (unit === '%' ? 1 : 0.1), 100)}%` }}
        />
      </div>
    </div>
  );
};

export default FinancialCard;