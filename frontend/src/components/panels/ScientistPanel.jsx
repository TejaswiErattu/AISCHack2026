import React, { useMemo } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, ReferenceLine 
} from 'recharts';
import { MOCK_FINANCIAL, MOCK_CLIMATE, MOCK_NARRATIVES } from '../../data/mockData';
import { useCountUp } from '../../hooks/useCountUp';
import AINarrative from '../shared/AINarrative';

const ScientistPanel = ({ 
  climateData = MOCK_CLIMATE, 
  narrative = MOCK_NARRATIVES.scientist 
}) => {
  // Generate 14 days of historical data showing a declining trend
  const chartData = useMemo(() => {
    return Array.from({ length: 14 }).map((_, i) => ({
      date: `02/${String(i + 14).padStart(2, '0')}`,
      ndvi: 70 - (i * 1.8) + (Math.random() * 3),
      soil: 65 - (i * 2.5) + (Math.random() * 4),
    }));
  }, []);

  const indices = [
    { label: 'Heat Stress Index', value: 67.3, unit: '/100' },
    { label: 'Drought Index', value: 54.1, unit: '/100' },
    { label: 'Rainfall Anomaly', value: -34, unit: '%' },
    { label: 'NDVI Health Score', value: 48, unit: '/100' },
    { label: 'Soil Moisture Deficit', value: 31, unit: '/100' },
  ];

  return (
    <div className="flex flex-col gap-6 animate-panel-entry font-mono">
      {/* 1. RAW INDEX CARDS ROW */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {indices.map((idx) => (
          <IndexCard key={idx.label} {...idx} />
        ))}
      </div>

      {/* 2. YIELD STRESS FORMULA BREAKDOWN (Hero Element) */}
      <div className="bg-[#111827] border border-border rounded-card p-5">
        <div className="flex justify-between items-center mb-4 border-b border-border pb-2">
          <h3 className="text-[10px] text-text-muted uppercase tracking-widest">
            yield_stress_score = Σ(weight_i × index_i)
          </h3>
          <span className="text-[9px] text-accent-primary opacity-70">v2.4_ENGINE_STABLE</span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] border-collapse">
            <thead>
              <tr className="text-text-muted border-b border-border/30">
                <th className="py-2 font-medium">COMPONENT</th>
                <th className="py-2 font-medium text-right">WEIGHT</th>
                <th className="py-2 font-medium text-right">VALUE</th>
                <th className="py-2 font-medium text-right">CONTRIB.</th>
              </tr>
            </thead>
            <tbody className="text-text-secondary">
              <FormulaRow label="Heat Stress" weight="0.30" val="67.3" contrib="20.2" />
              <FormulaRow label="Drought Index" weight="0.25" val="54.1" contrib="13.5" />
              <FormulaRow label="Rainfall Anom" weight="0.20" val="41.0" contrib="8.2" />
              <FormulaRow label="NDVI Health" weight="0.15" val="52.0" contrib="7.8" />
              <FormulaRow label="Soil Moisture" weight="0.10" val="38.5" contrib="3.9" />
              <tr className="border-t border-accent-primary/30 text-accent-primary font-bold">
                <td className="py-3">COMPOSITE SCORE</td>
                <td colSpan="2"></td>
                <td className="py-3 text-right text-[16px]">{climateData.yield_stress_score.toFixed(1)} / 100</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. TIME SERIES CHART (NDVI + SOIL) */}
      <div className="bg-[#111827] border border-border rounded-card p-4">
        <h3 className="text-[10px] text-text-muted uppercase tracking-widest mb-4">
          Atmospheric & Edaphic Time Series (14D)
        </h3>
        <div className="h-[160px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E3A5F" vertical={false} />
              <XAxis 
                dataKey="date" 
                stroke="#475569" 
                fontSize={10} 
                tickLine={false} 
                axisLine={false} 
              />
              <YAxis 
                domain={[0, 100]} 
                stroke="#475569" 
                fontSize={10} 
                tickLine={false} 
                axisLine={false} 
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1A2235', border: '1px solid #1E3A5F', borderRadius: '8px' }}
                itemStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }}
              />
              <ReferenceLine y={50} stroke="#475569" strokeDasharray="3 3" label={{ value: 'STRESS', fill: '#475569', fontSize: 9, position: 'insideRight' }} />
              <Line type="monotone" dataKey="ndvi" stroke="#10B981" strokeWidth={2} dot={false} animationDuration={1000} />
              <Line type="monotone" dataKey="soil" stroke="#3B82F6" strokeWidth={2} dot={false} animationDuration={1000} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. AI NARRATIVE (Scientific) */}
      <AINarrative text={narrative} mode="technical" />
    </div>
  );
};

// Internal Sub-components for cleaner structure
const IndexCard = ({ label, value, unit }) => {
  const animatedValue = useCountUp(value, 800);
  const color = value > 75 ? '#EF4444' : value > 50 ? '#F59E0B' : '#10B981';

  return (
    <div className="bg-background-card border border-border p-3 rounded-md flex flex-col gap-2">
      <span className="text-[9px] text-text-muted uppercase leading-tight h-[18px] overflow-hidden">
        {label}
      </span>
      <div className="flex items-baseline gap-1">
        <span className="text-[20px] font-bold text-text-primary">
          {animatedValue.toFixed(1)}
        </span>
        <span className="text-[10px] text-text-muted">{unit}</span>
      </div>
      <div className="w-full h-1 bg-background-secondary rounded-full overflow-hidden">
        <div 
          className="h-full transition-all duration-1000" 
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
};

const FormulaRow = ({ label, weight, val, contrib }) => (
  <tr className="border-b border-border/10 hover:bg-white/5 transition-colors">
    <td className="py-2 text-text-primary">{label}</td>
    <td className="py-2 text-right text-text-muted">{weight}</td>
    <td className="py-2 text-right text-text-secondary">× {val}</td>
    <td className="py-2 text-right text-accent-primary">= {contrib}</td>
  </tr>
);

export default ScientistPanel;