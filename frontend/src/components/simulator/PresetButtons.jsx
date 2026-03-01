import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';

const PRESETS = [
  { id: 'dust_bowl', label: 'Dust Bowl', icon: '🌵', color: 'border-accent-danger' },
  { id: 'deluge', label: 'The Deluge', icon: '🌊', color: 'border-accent-financial' },
  { id: 'frost', label: 'Late Frost', icon: '🌨️', color: 'border-purple-500' },
  { id: 'baseline', label: 'Baseline', icon: '📊', color: 'border-accent-positive' },
];

const PresetButtons = () => {
  const { applyPreset } = useContext(AppContext);

  return (
    <div className="grid grid-cols-2 gap-2">
      {PRESETS.map((preset) => (
        <button
          key={preset.id}
          onClick={() => applyPreset(preset.id)}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-button bg-background-card 
            border border-border hover:border-text-muted transition-all text-left
            active:scale-95 group
          `}
        >
          <span className="text-sm">{preset.icon}</span>
          <span className="text-[11px] font-bold text-text-secondary group-hover:text-text-primary uppercase tracking-tighter">
            {preset.label}
          </span>
        </button>
      ))}
    </div>
  );
};

export default PresetButtons;