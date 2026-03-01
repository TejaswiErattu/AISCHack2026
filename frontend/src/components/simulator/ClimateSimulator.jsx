import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';
import StressSlider from './StressSlider';
import PresetButtons from './PresetButtons';
import { useCountUp } from '../../hooks/useCountUp';

const ClimateSimulator = () => {
  const { 
    simulatorValues, 
    updateSimulator, 
    resetSimulator, 
    financialOutputs,
    climateData 
  } = useContext(AppContext);

  // Animate the simulation impact values
  const animatedImpact = useCountUp(financialOutputs?.delta_from_baseline ?? 0, 400);

  return (
    <div className="h-[140px] w-full bg-background-secondary border-t border-border px-6 py-4 flex items-center gap-8 shadow-[0_-10px_30px_rgba(0,0,0,0.5)] z-[3000]">
      
      {/* LEFT: SLIDERS (3 Column Grid) */}
      <div className="flex-1 grid grid-cols-3 gap-6 pr-8 border-r border-border/50">
        <StressSlider 
          label="Temp Anomaly" 
          value={simulatorValues.temperature} 
          min={-3} max={5} step={0.1} unit="°C"
          icon="🌡️"
          gradient="from-blue-500 via-background-elevated to-red-500"
          onChange={(v) => updateSimulator('temperature', v)}
        />
        <StressSlider 
          label="Drought Index" 
          value={simulatorValues.drought} 
          min={0} max={100} step={1} unit=""
          icon="☀️"
          gradient="from-accent-positive via-accent-warning to-accent-danger"
          onChange={(v) => updateSimulator('drought', v)}
        />
        <StressSlider 
          label="Rainfall Anomaly" 
          value={simulatorValues.rainfall} 
          min={-80} max={80} step={1} unit="%"
          icon="🌧️"
          gradient="from-accent-warning via-background-elevated to-blue-500"
          onChange={(v) => updateSimulator('rainfall', v)}
        />
      </div>

      {/* CENTER: PRESET TOGGLES */}
      <div className="w-[300px] flex flex-col gap-3">
        <h4 className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em]">Climate Archetypes</h4>
        <PresetButtons />
      </div>

      {/* RIGHT: IMPACT SUMMARY */}
      <div className="w-[240px] bg-background-primary/50 rounded-card border border-border p-3 flex flex-col justify-between relative">
        <div className="flex justify-between items-start">
          <span className="text-[10px] font-bold text-text-muted uppercase">Simulation Impact</span>
          <button 
            onClick={resetSimulator}
            className="text-[10px] text-accent-primary hover:underline font-bold uppercase tracking-tighter"
          >
            ↺ Reset
          </button>
        </div>
        
        <div className="space-y-1 mt-2">
          <div className="flex justify-between items-baseline">
            <span className="text-[11px] text-text-secondary">Stress Score</span>
            <span className="font-mono text-[14px] font-bold text-accent-danger">
              {(climateData?.yield_stress_score ?? 0).toFixed(1)} → {Math.round((climateData?.yield_stress_score ?? 0) + (animatedImpact * 10))}
            </span>
          </div>
          <div className="flex justify-between items-baseline">
            <span className="text-[11px] text-text-secondary">Interest Rate</span>
            <span className="font-mono text-[14px] font-bold text-accent-danger">
              {financialOutputs.interest_rate}% <span className="text-[11px]">↑+{animatedImpact.toFixed(1)}%</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClimateSimulator;