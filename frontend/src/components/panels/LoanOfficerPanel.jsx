import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';
import { useCountUp } from '../../hooks/useCountUp';
import StressGauge from '../shared/StressGauge';
import AINarrative from '../shared/AINarrative';

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

const computeFactors = (climate) => {
  if (!climate) return [];
  const heat = clamp((climate.temperature_anomaly + 3) / 8 * 100, 0, 100);
  const drought = clamp(climate.drought_index, 0, 100);
  const rain = clamp(Math.abs(climate.rainfall_anomaly) / 80 * 100, 0, 100);
  const ndvi = clamp(100 - (climate.ndvi_score ?? 50), 0, 100);
  const soil = clamp(100 - (climate.soil_moisture ?? 50), 0, 100);

  const weighted = [
    { label: "Heat Stress Index", val: heat, w: 0.30, color: "#EF4444" },
    { label: "Drought Index",     val: drought, w: 0.25, color: "#F59E0B" },
    { label: "Rainfall Anomaly",  val: rain, w: 0.20, color: "#3B82F6" },
    { label: "Vegetation (NDVI)", val: ndvi, w: 0.15, color: "#10B981" },
  ];
  const totalStress = weighted.reduce((s, f) => s + f.w * f.val, 0) + 0.10 * soil;

  return weighted.map(f => ({
    ...f,
    pct: totalStress > 0 ? Math.round((f.w * f.val) / totalStress * 100) : 0,
  }));
};

const LoanOfficerPanel = () => {
  const { financialOutputs, climateData, narratives, isLoading } = useContext(AppContext);

  const animatedRate = useCountUp(financialOutputs?.interest_rate ?? 0, 800);
  const animatedPD = useCountUp((financialOutputs?.probability_of_default ?? 0) * 100, 800);
  const factors = computeFactors(climateData);

  if (isLoading) return <LoanOfficerSkeleton />;

  if (!financialOutputs || !climateData) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-black text-[#475569] font-mono text-sm">
        <p className="animate-pulse">{"<"} SELECT A REGION ON MAP TO INITIALIZE TERMINAL {">"}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#000000] text-[#F1F5F9] font-mono select-none">
      
      {/* 1. TICKER HEADER */}
      <div className="flex items-center justify-between bg-[#0D1117] px-3 py-1 border-b border-[#1a1a1a]">
        <div className="flex gap-4 items-center">
          <span className="bg-[#F59E0B] text-black px-1 text-[11px] font-bold">HOT US Equity</span>
          <span className="text-[#00D4AA] text-[11px]">91) Talk2Desk</span>
        </div>
        <div className="text-[#EF4444] text-[11px] font-bold">
          TRADEBOOK STRATEGY ANALYZER
        </div>
      </div>

      {/* 2. RISK GAUGE SECTION */}
      <div className="flex justify-between items-start p-4 bg-black">
        <div className="flex flex-col">
          <h2 className="text-[#94A3B8] text-[12px] uppercase tracking-tighter">Current Risk Assessment</h2>
          <div className="text-[10px] text-[#475569] mt-1">VOL: 1.8MMM | SOURCE: TERRALEND</div>
        </div>
        <div className="transform scale-90 origin-top-right">
          <StressGauge score={climateData?.yield_stress_score ?? 0} />
        </div>
      </div>

      {/* 3. BLOOMBERG DATA TABLE */}
      <div className="w-full border-t border-[#1a1a1a]">
        <div className="grid grid-cols-12 bg-[#0D1117] py-1 px-3 text-[10px] text-[#475569] uppercase font-bold">
          <div className="col-span-5">Risk Factor</div>
          <div className="col-span-4 text-right">Value</div>
          <div className="col-span-3 text-right">Delta</div>
        </div>

        <TableRow label="INTEREST RATE" value={`${animatedRate.toFixed(1)}%`} delta={financialOutputs?.delta_from_baseline ?? 0} isPercent />
        <TableRow label="PROBABILITY DEFAULT" value={`${animatedPD.toFixed(1)}%`} delta={2.4} isEven />
        <TableRow label="INSURANCE PREMIUM" value={`$${(financialOutputs?.insurance_premium ?? 0).toLocaleString()}`} delta={290} />
        <TableRow label="REPAYMENT FLEX" value={`${financialOutputs?.repayment_flexibility ?? '--'}/100`} delta={-12} isEven />
        <TableRow label="AI RATE FLOOR" value={`${financialOutputs?.rate_floor ?? '--'}%`} delta={0} />
        <TableRow label="AI RATE CEILING" value={`${financialOutputs?.rate_ceiling ?? '--'}%`} delta={0} isEven />
      </div>

      {/* 4. DOMINANT RISK FACTORS */}
      <div className="mt-6 px-3">
        <div className="text-[11px] text-[#475569] mb-2 border-b border-[#1a1a1a] pb-1">RISK_FACTOR_CONTRIBUTION</div>
        <div className="space-y-1 text-[11px]">
          {factors.map(f => (
            <FactorRow key={f.label} label={f.label} val={f.val.toFixed(1)} pct={f.pct} color={f.color} />
          ))}
        </div>
      </div>

      {/* 5. TERMINAL NARRATIVE */}
      <div className="mt-auto p-3">
        <div className="bg-[#0D1117] border border-[#1a1a1a] p-3">
          <div className="text-[#10B981] text-[10px] mb-2 font-bold">{'>'} RISK_ANALYSIS_ENGINE</div>
          <p className="text-[#94A3B8] text-[12px] leading-relaxed">
            {narratives?.loan_officer}
          </p>
        </div>
      </div>

      {/* 6. FUNCTION KEY ACTIONS */}
      <div className="flex gap-2 p-3 border-t border-[#1a1a1a]">
        <button className="flex-1 bg-[#1a1a1a] border border-[#333333] py-1 text-[11px] hover:bg-[#222222] transition-colors">
          <span className="text-[#00D4AA] mr-2">[F1]</span>GENERATE PROPOSAL
        </button>
        <button className="flex-1 bg-[#1a1a1a] border border-[#333333] py-1 text-[11px] hover:bg-[#222222] transition-colors">
          <span className="text-[#00D4AA] mr-2">[F2]</span>EXPORT MEMO
        </button>
      </div>
    </div>
  );
};

const TableRow = ({ label, value, delta, isEven, isPercent }) => (
  <div className={`grid grid-cols-12 py-1.5 px-3 text-[12px] ${isEven ? 'bg-[#080808]' : 'bg-black'}`}>
    <div className="col-span-5 text-[#94A3B8]">{label}</div>
    <div className="col-span-4 text-right font-bold text-[#F1F5F9]">{value}</div>
    <div className={`col-span-3 text-right ${delta > 0 ? 'text-[#EF4444]' : delta < 0 ? 'text-[#10B981]' : 'text-[#475569]'}`}>
      {delta !== 0 && (delta > 0 ? '▲' : '▼')} {delta !== 0 && (isPercent ? `+${delta}%` : delta)}
    </div>
  </div>
);

const FactorRow = ({ label, val, pct, color }) => {
  const blocks = Math.floor(pct / 5);
  return (
    <div className="grid grid-cols-12 items-center gap-2">
      <div className="col-span-4 text-[#94A3B8]">{label}</div>
      <div className="col-span-2 text-right">{val}</div>
      <div className="col-span-5 font-mono tracking-tighter" style={{ color }}>
        {"█".repeat(blocks)}{"░".repeat(20 - blocks)}
      </div>
      <div className="col-span-1 text-right text-[#475569]">{pct}%</div>
    </div>
  );
};

const LoanOfficerSkeleton = () => (
  <div className="bg-black h-full w-full" />
);

export default LoanOfficerPanel;