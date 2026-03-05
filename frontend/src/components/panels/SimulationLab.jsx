import React, { useState, useContext } from 'react';
import { MOCK_SIMULATION } from '../../data/mockData';
import { AppContext } from '../../context/AppContext';
import { api } from '../../api/client';
import { useCountUp } from '../../hooks/useCountUp';

const SimulationLab = ({ regionId, financialOutputs }) => {
  const { selectedRegion, setIsDemoMode } = useContext(AppContext);
  const [gameState, setGameState] = useState('IDLE');
  const [stepsCompleted, setStepsCompleted] = useState(0);
  const [results, setResults] = useState(MOCK_SIMULATION);

  const runSimulation = async () => {
    if (!selectedRegion) return;
    setGameState('RUNNING');
    setStepsCompleted(0);

    // Start progress animation
    const timers = [500, 1000, 1500, 2000].map((ms, index) =>
      setTimeout(() => setStepsCompleted(index + 1), ms)
    );

    // Fetch real batch results in parallel with animation
    const regionId = selectedRegion.region_id || selectedRegion.id;
    const batchResults = await api.runBatchSimulation(regionId, setIsDemoMode);
    setResults(batchResults);

    // Wait for animation to finish before showing results
    setTimeout(() => setGameState('RESULTS'), 2800);
  };

  const resetSim = () => {
    setGameState('IDLE');
    setStepsCompleted(0);
  };

  const downloadMemo = () => {
    const regionId = selectedRegion.region_id || selectedRegion.id;
    window.open(api.getMemoUrl(regionId), '_blank');
  };

  if (gameState === 'IDLE') return <IdleState onRun={runSimulation} region={selectedRegion} />;
  if (gameState === 'RUNNING') return <RunningState steps={stepsCompleted} />;
  return <ResultsState data={results} onReset={resetSim} onDownload={downloadMemo} />;
};

// --- STATE 1: IDLE ---
const IdleState = ({ onRun, region }) => (
  <div className="h-full flex flex-col items-center justify-center text-center p-4 sm:p-8 animate-fade-in">
    {region && (
      <span className="text-[10px] sm:text-[11px] font-bold text-accent-primary uppercase tracking-[0.2em] mb-2">
        {region.name} • {region.primary_crop}
      </span>
    )}
    <h2 className="text-[20px] sm:text-[24px] font-bold text-text-primary mb-3 sm:mb-4">Climate Stress Test</h2>
    <p className="text-[12px] sm:text-[14px] text-text-muted max-w-[360px] leading-relaxed mb-6 sm:mb-8">
      Run this farm through 4 decades of climate scenarios. See exactly how volatile conditions reshape this loan.
    </p>
    <button
      onClick={onRun}
      disabled={!region}
      className={`
        h-[44px] sm:h-[52px] w-[200px] sm:w-[240px] rounded-[12px] font-bold text-[14px] sm:text-[16px] transition-all
        ${region
          ? 'bg-gradient-to-r from-accent-primary to-accent-financial text-background-primary shadow-glow-teal hover:scale-105 active:scale-95'
          : 'bg-background-elevated text-text-muted cursor-not-allowed border border-border'}
      `}
    >
      ▶ Run Climate Stress Test
    </button>
    <p className="mt-3 sm:mt-4 text-[10px] sm:text-[11px] text-text-muted uppercase tracking-widest">
      4 climate archetypes · ~3 seconds
    </p>
  </div>
);

// --- STATE 2: RUNNING ---
const RunningState = ({ steps }) => {
  const progressRows = [
    { label: "Dust Bowl Echo", sub: "Severe Drought" },
    { label: "The Deluge", sub: "Flash Flood" },
    { label: "Late Frost", sub: "Temperature Snap" },
    { label: "Baseline", sub: "Seasonal Norms" }
  ];

  return (
    <div className="h-full flex flex-col justify-center p-6 sm:p-10 animate-fade-in">
      <div className="space-y-4 sm:space-y-6">
        {progressRows.map((row, i) => (
          <div key={row.label} className={`flex items-center gap-4 transition-all duration-500 ${steps > i ? 'opacity-100' : 'opacity-20'}`}>
            <div className="w-5 h-5 flex items-center justify-center">
              {steps > i ? (
                <span className="text-accent-positive font-bold">✓</span>
              ) : (
                <div className="w-3 h-3 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            <div className="font-mono">
              <span className="text-[13px] text-text-primary font-bold">{row.label}</span>
              <span className="text-[11px] text-text-muted ml-3">({row.sub})</span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-12 h-1.5 w-full bg-background-card rounded-full overflow-hidden">
        <div
          className="h-full bg-accent-primary transition-all duration-[2000ms] ease-linear"
          style={{ width: `${(steps / 4) * 100}%` }}
        />
      </div>
    </div>
  );
};

// --- STATE 3: RESULTS ---
const ResultsState = ({ data, onReset, onDownload }) => {
  const sortedData = [...data].sort((a, b) => b.stress_score - a.stress_score);

  // Compute resilience report values from actual results
  const rates = data.map(s => s.interest_rate);
  const bestRate = Math.min(...rates);
  const worstRate = Math.max(...rates);
  const avgRate = rates.reduce((a, b) => a + b, 0) / rates.length;

  // Find floor/ceiling from the lowest-stress and highest-stress scenarios
  const sortedByStress = [...data].sort((a, b) => a.stress_score - b.stress_score);
  const floorRate = sortedByStress[0]?.interest_rate ?? bestRate;
  const ceilingRate = sortedByStress[sortedByStress.length - 1]?.interest_rate ?? worstRate;

  return (
    <div className="space-y-6 pb-8 animate-fade-in font-sans">
      <div className="flex flex-col border-b border-border/30">
        <div className="flex items-center px-1 pb-2 mb-1 border-b border-border/30">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
            Simulation Results · 4 Scenarios
          </span>
        </div>
        {sortedData.map((scenario, i) => (
          <ScenarioCard key={scenario.name} scenario={scenario} index={i} />
        ))}
      </div>

      <div className="bg-[#111827] border-t-2 border-accent-primary p-4 sm:p-6 rounded-b-card shadow-xl">
        <h3 className="text-[10px] sm:text-[11px] font-bold text-accent-primary uppercase tracking-widest mb-4 sm:mb-6">
          Climate Resilience Report
        </h3>

        <div className="flex gap-4 sm:gap-8 mb-6 sm:mb-8">
          <div className="flex flex-col">
            <p className="text-[9px] sm:text-[10px] uppercase text-text-muted font-bold tracking-tight mb-1">Best Case</p>
            <p className="text-[22px] sm:text-[32px] font-mono font-bold text-accent-positive leading-none">{bestRate.toFixed(1)}%</p>
          </div>
          <div className="flex flex-col">
            <p className="text-[9px] sm:text-[10px] uppercase text-text-muted font-bold tracking-tight mb-1">Most Likely</p>
            <p className="text-[22px] sm:text-[32px] font-mono font-bold text-accent-warning leading-none">{avgRate.toFixed(1)}%</p>
          </div>
          <div className="flex flex-col">
            <p className="text-[9px] sm:text-[10px] uppercase text-text-muted font-bold tracking-tight mb-1">Worst Case</p>
            <p className="text-[22px] sm:text-[32px] font-mono font-bold text-accent-danger leading-none">{worstRate.toFixed(1)}%</p>
          </div>
        </div>

        <div className="border-t border-border/20 pt-4 flex flex-wrap items-center gap-4 sm:gap-6 mb-6 font-mono text-[10px] sm:text-[12px]">
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Floor</span>
            <span className="text-text-muted opacity-30">──</span>
            <span className="text-accent-primary font-bold">{floorRate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Ceiling</span>
            <span className="text-text-muted opacity-30">──</span>
            <span className="text-accent-warning font-bold">{ceilingRate.toFixed(1)}%</span>
          </div>
        </div>

        <p className="text-[13px] text-text-secondary leading-relaxed">
          {worstRate - bestRate > 2
            ? `High rate volatility of ${(worstRate - bestRate).toFixed(1)}% across scenarios indicates significant climate exposure. Strategic risk mitigation could narrow this spread.`
            : `Moderate rate stability across scenarios (${(worstRate - bestRate).toFixed(1)}% spread) suggests reasonable climate resilience for this region.`
          }
        </p>
      </div>

      <div className="flex items-center gap-6 px-1">
        <button
          onClick={onDownload}
          className="text-[12px] font-mono text-accent-primary hover:underline transition-all"
        >
          ↓ export risk_memo.txt
        </button>
        <button
          onClick={onReset}
          className="text-[12px] font-mono text-text-muted hover:text-text-primary hover:underline transition-all"
        >
          ↺ run_simulation_again
        </button>
      </div>
    </div>
  );
};

const ScenarioCard = ({ scenario, index }) => {
  const rate = useCountUp(scenario.interest_rate, 1000);

  const severity = scenario.stress_score > 90 ? 'CRITICAL' :
                   scenario.stress_score > 70 ? 'SEVERE' :
                   scenario.stress_score > 50 ? 'ELEVATED' : 'MODERATE';

  return (
    <div
      className="flex items-center h-auto sm:h-[36px] px-2 py-2 sm:py-0 border-b border-border/10 hover:bg-white/[0.02] transition-colors flex-wrap sm:flex-nowrap"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div
        className="w-2 h-2 rounded-full mr-3 sm:mr-4 shrink-0"
        style={{ backgroundColor: scenario.color }}
      />
      <div className="flex flex-col sm:flex-row sm:items-center flex-1 font-mono text-[11px] sm:text-[12px] min-w-0">
        <span className="text-text-primary font-bold sm:w-40 truncate">{scenario.name}</span>
        <div className="flex items-center gap-3 sm:gap-4 text-text-muted">
          <div className="flex items-center gap-1">
            <span className="opacity-50">Rate:</span>
            <span className="text-text-secondary font-bold">{rate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="opacity-50">PD:</span>
            <span className="text-text-secondary font-bold">{(scenario.pd * 100).toFixed(0)}%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="opacity-50">Stress:</span>
            <span className="text-text-secondary font-bold">{scenario.stress_score}</span>
          </div>
        </div>
      </div>
      <span
        className="text-[10px] sm:text-[11px] font-bold shrink-0 font-mono ml-auto sm:ml-0"
        style={{ color: scenario.color }}
      >
        {severity}
      </span>
    </div>
  );
};

export default SimulationLab;
