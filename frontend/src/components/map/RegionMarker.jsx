import React, { useContext, useMemo } from 'react';
import { Marker, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { AppContext } from '../../context/AppContext';

const OVERLAY_COLORS = {
  ndvi: '#10B981',
  soil: '#3B82F6',
  temp: '#EF4444',
  rain: '#8B5CF6',
};

const getStressColor = (score) => {
  if (score <= 25) return '#10B981';
  if (score <= 50) return '#F59E0B';
  if (score <= 75) return '#F97316';
  return '#EF4444';
};

// Inject pulse keyframe once into document head
if (typeof document !== 'undefined' && !document.getElementById('pulse-style')) {
  const style = document.createElement('style');
  style.id = 'pulse-style';
  style.innerHTML = `
    @keyframes markerPulse {
      0% { r: 14; opacity: 0.8; }
      100% { r: 26; opacity: 0; }
    }
    .pulse-ring {
      animation: markerPulse 1.4s ease-out infinite;
    }
  `;
  document.head.appendChild(style);
}

const RegionMarker = ({ region }) => {
  const { selectedRegion, setSelectedRegion, activeOverlays } = useContext(AppContext);
  const isSelected = selectedRegion?.id === region.id;
  const baseColor = getStressColor(region.stress_score);

  const customIcon = useMemo(() => {
    const baseSize = isSelected ? 20 : 16;
    const ringSpacing = 4;
    const ringThickness = 2;
    const pulseExtra = isSelected ? 30 : 0;
    const totalSize = baseSize + (activeOverlays.length * (ringSpacing * 2)) + pulseExtra;
    const center = totalSize / 2;

    const ringsSvg = activeOverlays.map((overlayId, index) => {
      const radius = (baseSize / 2) + ((index + 1) * ringSpacing);
      return `
        <circle
          cx="${center}" cy="${center}" r="${radius}"
          fill="none"
          stroke="${OVERLAY_COLORS[overlayId]}"
          stroke-width="${ringThickness}"
          stroke-opacity="0.6"
        />`;
    }).join('');

    const pulseSvg = isSelected ? `
      <circle
        cx="${center}" cy="${center}" r="14"
        fill="none"
        stroke="#00D4AA"
        stroke-width="2"
        stroke-opacity="0.8"
        class="pulse-ring"
      />
      <circle
        cx="${center}" cy="${center}" r="14"
        fill="none"
        stroke="#00D4AA"
        stroke-width="2"
        stroke-opacity="0.5"
        class="pulse-ring"
        style="animation-delay: 0.5s"
      />
    ` : '';

    const html = `
      <div style="width: ${totalSize}px; height: ${totalSize}px; position: relative;">
        <svg width="${totalSize}" height="${totalSize}" style="position: absolute; top: 0; left: 0; overflow: visible;">
          ${pulseSvg}
          ${ringsSvg}
          <circle
            cx="${center}" cy="${center}" r="${baseSize / 2}"
            fill="${baseColor}"
            stroke="${isSelected ? '#00D4AA' : '#FFFFFF'}"
            stroke-width="${isSelected ? 3 : 2}"
            style="filter: ${isSelected ? `drop-shadow(0 0 8px ${baseColor}99)` : 'none'}; transition: all 0.2s ease;"
          />
        </svg>
      </div>
    `;

    return L.divIcon({
      html,
      className: 'custom-marker-container',
      iconSize: [totalSize, totalSize],
      iconAnchor: [center, center],
    });
  }, [isSelected, baseColor, activeOverlays]);

  return (
    <Marker
      position={[region.lat, region.lng]}
      icon={customIcon}
      eventHandlers={{ click: () => setSelectedRegion(region) }}
    >
      <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent={isSelected}>
        <div className="bg-background-card border border-border px-2 py-1 rounded shadow-glow-teal">
          <p className="text-[11px] font-bold text-text-primary whitespace-nowrap">{region.name}</p>
          <p className="text-[9px] text-text-secondary uppercase tracking-tighter">
            {region.primary_crop} • {region.stress_score}/100
          </p>
        </div>
      </Tooltip>
    </Marker>
  );
};

export default RegionMarker;