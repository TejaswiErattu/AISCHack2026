import React, { useState } from 'react';

const StressSlider = ({ label, value, min, max, step, unit, icon, gradient, onChange }) => {
  const [localValue, setLocalValue] = useState(value);

  const handleDrag = (e) => {
    const val = parseFloat(e.target.value);
    setLocalValue(val);
  };

  const handleRelease = () => {
    onChange(localValue);
  };

  return (
    <div className="flex flex-col gap-3 group">
      <div className="flex justify-between items-end">
        <label className="text-[10px] font-bold text-text-muted uppercase tracking-wider flex items-center gap-1">
          <span>{icon}</span> {label}
        </label>
        <span className="font-mono text-[14px] font-bold text-text-primary">
          {localValue > 0 ? '+' : ''}{localValue}{unit}
        </span>
      </div>
      
      <div className="relative h-6 flex items-center">
        {/* Custom Track Background */}
        <div className={`absolute w-full h-1.5 rounded-full bg-gradient-to-r ${gradient} opacity-40`} />
        
        <input 
          type="range"
          min={min} max={max} step={step}
          value={localValue}
          onChange={handleDrag}
          onMouseUp={handleRelease}
          onTouchEnd={handleRelease}
          className="absolute w-full h-1.5 bg-transparent appearance-none cursor-pointer z-10
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white 
            [&::-webkit-slider-thumb]:shadow-[0_0_10px_rgba(0,212,170,0.6)] 
            [&::-webkit-slider-thumb]:hover:scale-125 transition-transform"
        />
      </div>
    </div>
  );
};

export default StressSlider;