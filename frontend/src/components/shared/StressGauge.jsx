import React from 'react';
import { useCountUp } from '../../hooks/useCountUp';

const StressGauge = ({ score }) => {
  const animatedScore = useCountUp(score, 800);
  const rotation = (animatedScore / 100) * 180 - 90; // Map 0-100 to -90 to 90 deg

  const getStatusText = (s) => {
    if (s <= 25) return { label: 'LOW', color: 'text-accent-positive' };
    if (s <= 50) return { label: 'MODERATE', color: 'text-accent-warning' };
    if (s <= 75) return { label: 'ELEVATED', color: 'text-accent-danger' };
    return { label: 'SEVERE', color: 'text-red-600' };
  };

  const status = getStatusText(score);

  return (
    <div className="relative w-[200px] h-[110px] flex flex-col items-center overflow-hidden">
      <svg width="200" height="110" viewBox="0 0 200 110">
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="50%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#EF4444" />
          </linearGradient>
        </defs>
        {/* Track */}
        <path d="M20,100 A80,80 0 0,1 180,100" fill="none" stroke="#1A2235" strokeWidth="12" strokeLinecap="round" />
        {/* Fill */}
        <path 
          d="M20,100 A80,80 0 0,1 180,100" 
          fill="none" 
          stroke="url(#gaugeGradient)" 
          strokeWidth="12" 
          strokeLinecap="round"
          strokeDasharray={`${(animatedScore / 100) * 251.3} 251.3`}
        />
        {/* Needle */}
        <line 
          x1="100" y1="100" x2="100" y2="30" 
          stroke="white" strokeWidth="2" 
          style={{ transform: `rotate(${rotation}deg)`, transformOrigin: '100px 100px', transition: 'transform 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute bottom-2 flex flex-col items-center">
        <span className="font-mono text-[32px] font-bold leading-none">{Math.round(animatedScore)}</span>
        <span className={`text-[10px] font-bold tracking-[0.2em] mt-1 ${status.color}`}>{status.label}</span>
      </div>
    </div>
  );
};

export default StressGauge;