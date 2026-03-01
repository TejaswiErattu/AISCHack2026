import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';

const OVERLAYS = [
  { id: 'ndvi', label: '🌿 NDVI', description: 'Vegetation Health' },
  { id: 'soil', label: '💧 Soil Moisture', description: 'Soil Saturation' },
  { id: 'temp', label: '🌡️ Temperature', description: 'Heat Anomaly' },
  { id: 'rain', label: '🌧️ Rainfall', description: 'Precipitation' },
];

const OverlayToggles = () => {
  const { activeOverlays, toggleOverlay } = useContext(AppContext);

  return (
    <div className="flex flex-col gap-2 bg-background-secondary/80 backdrop-blur-md p-2 rounded-lg border border-border shadow-2xl">
      {OVERLAYS.map((overlay) => {
        const isActive = activeOverlays.includes(overlay.id);
        return (
          <button
            key={overlay.id}
            onClick={() => toggleOverlay(overlay.id)}
            className={`
              flex items-center px-3 py-2 rounded-md transition-all duration-200 group
              ${isActive 
                ? 'bg-background-elevated border-accent-primary border' 
                : 'bg-background-card border-transparent border hover:bg-background-elevated'}
            `}
          >
            <span className={`text-[11px] font-semibold uppercase tracking-wider transition-colors
              ${isActive ? 'text-text-primary' : 'text-text-muted group-hover:text-text-secondary'}
            `}>
              {overlay.label}
            </span>
            {isActive && (
              <div className="ml-2 w-1.5 h-1.5 rounded-full bg-accent-primary animate-pulse" />
            )}
          </button>
        );
      })}
    </div>
  );
};

export default OverlayToggles;