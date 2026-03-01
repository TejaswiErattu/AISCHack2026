import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';
import { useCountUp } from '../../hooks/useCountUp';
import AINarrative from '../shared/AINarrative';

const FarmerPanel = () => {
  const { financialOutputs, climateData, narratives, isLoading } = useContext(AppContext);
  const animatedRate = useCountUp(financialOutputs.interest_rate, 800);
  const isRateHigher = financialOutputs.delta_from_baseline > 0;

  // Logic to translate raw data into human sentences
  const getImpactFactors = () => {
    const factors = [
      { 
        id: 'temp', 
        icon: '🌡️', 
        text: "It's been unusually hot this season", 
        impact: climateData.temperature_anomaly > 2 ? 'HIGH' : 'MEDIUM',
        color: climateData.temperature_anomaly > 2 ? 'text-[#EF4444]' : 'text-[#F59E0B]'
      },
      { 
        id: 'drought', 
        icon: '☀️', 
        text: "Conditions have been quite dry lately", 
        impact: climateData.drought_index > 60 ? 'HIGH' : climateData.drought_index > 30 ? 'MEDIUM' : 'LOW',
        color: climateData.drought_index > 60 ? 'text-[#EF4444]' : climateData.drought_index > 30 ? 'text-[#F59E0B]' : 'text-[#10B981]'
      },
      { 
        id: 'soil', 
        icon: '💧', 
        text: "The ground is thirstier than usual", 
        impact: climateData.soil_moisture < 40 ? 'HIGH' : 'MEDIUM',
        color: climateData.soil_moisture < 40 ? 'text-[#EF4444]' : 'text-[#F59E0B]'
      },
      { 
        id: 'veg', 
        icon: '🌿', 
        text: "Your crops are showing signs of stress", 
        impact: climateData.ndvi_score < 50 ? 'HIGH' : 'MEDIUM',
        color: climateData.ndvi_score < 50 ? 'text-[#EF4444]' : 'text-[#F59E0B]'
      }
    ];
    return factors.slice(0, 4);
  };

  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  if (isLoading) return <div className="animate-pulse bg-[#0a0a0a] h-full" />;

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a] text-white font-sans animate-panel-entry p-4">
      
      {/* 1. CASH APP STYLE HERO RATE SECTION */}
      <div className="bg-[#1c1c1e] rounded-[24px] p-8 mb-6 flex flex-col items-center">
        <span className="text-[13px] text-[#94A3B8] font-medium mb-1">Your Rate Today</span>
        <div className="flex items-baseline mb-4">
          <span className="text-[72px] font-bold leading-none tracking-tight">
            {animatedRate.toFixed(1)}%
          </span>
        </div>
        
        {/* Wise-style inline comparison */}
        <div className="w-full border-t border-[#2c2c2e] pt-4 mt-2 space-y-1">
          <div className="flex justify-between text-[13px]">
            <span className="text-[#94A3B8]">Without TerraLend you'd pay</span>
            <span className="text-[#94A3B8] line-through">{financialOutputs.baseline_rate}%</span>
          </div>
          <div className="flex justify-between text-[13px]">
            <span className="text-white">Climate impact adjustment</span>
            <span className={isRateHigher ? 'text-[#EF4444]' : 'text-[#10B981]'}>
              {isRateHigher ? '+' : '-'}{Math.abs(financialOutputs.delta_from_baseline).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* 2. WISE STYLE IMPACT ROWS */}
      <div className="flex flex-col mb-8">
        <h3 className="text-[10px] text-[#475569] font-bold uppercase tracking-[0.2em] mb-4 ml-1">
          What's affecting your rate
        </h3>
        <div className="flex flex-col">
          {getImpactFactors().map((factor) => (
            <div key={factor.id} className="flex items-center py-4 border-b border-[#1E3A5F]/30 last:border-0 h-[64px]">
              <div className="w-[40px] text-xl">{factor.icon}</div>
              <div className="flex-1">
                <p className="text-[14px] text-[#F1F5F9] font-medium leading-tight">{factor.text}</p>
              </div>
              <div className={`text-[11px] font-bold font-mono ${factor.color}`}>
                {factor.impact}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. SEASONAL OUTLOOK (FLAT STRIP) */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-6 px-2">
          {dayLabels.map((day, i) => (
            <div key={day} className="flex flex-col items-center gap-3">
              <span className="text-[10px] text-[#475569] font-bold uppercase">{day}</span>
              <div className={`w-2 h-2 rounded-full ${i < 3 ? 'bg-[#EF4444]' : i < 5 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'}`} />
            </div>
          ))}
        </div>
        <p className="text-[13px] text-[#94A3B8] italic leading-relaxed text-center px-4">
          "Expect these tough conditions for another two weeks before relief arrives."
        </p>
      </div>

      {/* 4. AI NARRATIVE (MESSAGE STYLE) */}
      <div className="mt-auto">
        <div className="flex items-center gap-2 mb-2 ml-1">
          <span className="text-[10px] font-bold text-[#475569] uppercase tracking-widest">🌿 FROM TERRALEND</span>
        </div>
        <p className="text-[15px] text-[#94A3B8] leading-[1.7] font-sans">
          {narratives.farmer}
        </p>
      </div>
    </div>
  );
};

export default FarmerPanel;