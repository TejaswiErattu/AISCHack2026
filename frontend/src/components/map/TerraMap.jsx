import React, { useContext, useState } from 'react';
import { MapContainer, TileLayer, ZoomControl, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import RegionMarker from './RegionMarker';
import OverlayToggles from './OverlayToggles';
import { AppContext } from '../../context/AppContext';

const TILES = {
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    label: 'DARK'
  },
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; Esri &copy; NASA',
    label: 'SAT'
  }
};

// Invisible component that tracks mouse position on the map
const MouseTracker = ({ onMove }) => {
  useMapEvents({
    mousemove: (e) => onMove(e.latlng),
    mouseout: () => onMove(null)
  });
  return null;
};

const TerraMap = () => {
  const { activeOverlays, selectedRegion, regions } = useContext(AppContext);
  const [tileMode, setTileMode] = useState('dark');
  const [hoverCoords, setHoverCoords] = useState(null);

  const center = [39.8283, -98.5795];
  const tile = TILES[tileMode];

  // Find closest region to hovered coordinates for contextual info
  const getHoverRegion = () => {
    if (!hoverCoords) return null;
    return regions.reduce((closest, region) => {
      const dist = Math.hypot(region.lat - hoverCoords.lat, region.lng - hoverCoords.lng);
      const closestDist = closest ? Math.hypot(closest.lat - hoverCoords.lat, closest.lng - hoverCoords.lng) : Infinity;
      return dist < closestDist ? region : closest;
    }, null);
  };

  const hoverRegion = getHoverRegion();

  return (
    <div className="relative w-full h-full bg-background-primary overflow-hidden border-r border-border">
      <MapContainer
        center={center}
        zoom={4}
        zoomControl={false}
        className="w-full h-full"
        scrollWheelZoom={true}
      >
        <TileLayer
          key={tileMode}
          url={tile.url}
          attribution={tile.attribution}
        />

        <ZoomControl position="topright" />
        <MouseTracker onMove={setHoverCoords} />

        {regions.map((region) => (
          <RegionMarker
            key={region.id}
            region={region}
            activeOverlays={activeOverlays}
            isSelected={selectedRegion?.id === region.id}
          />
        ))}
      </MapContainer>

      {/* Tile Toggle — top left */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-1 bg-black/70 border border-white/10 backdrop-blur-sm px-2 py-1">
        {Object.entries(TILES).map(([key, val]) => (
          <button
            key={key}
            onClick={() => setTileMode(key)}
            className={`text-[10px] font-mono px-2 py-0.5 transition-colors ${
              tileMode === key
                ? 'bg-[#00D4AA] text-black font-bold'
                : 'text-[#94A3B8] hover:text-white'
            }`}
          >
            {val.label}
          </button>
        ))}
      </div>

      {/* Overlay Toggles — bottom left */}
      <div className="absolute bottom-8 left-3 z-[1000]">
        <OverlayToggles />
      </div>

      {/* NASA-style coordinate bar — bottom */}
      <div className="absolute bottom-0 left-0 right-0 z-[1000] bg-black/80 backdrop-blur-sm border-t border-white/10 px-3 py-1 flex items-center gap-4 font-mono text-[10px] text-[#475569]">
        {hoverCoords ? (
          <>
            <span className="text-[#00D4AA]">●</span>
            <span>LAT: <span className="text-[#94A3B8]">{hoverCoords.lat.toFixed(4)}</span></span>
            <span>LNG: <span className="text-[#94A3B8]">{hoverCoords.lng.toFixed(4)}</span></span>
            {hoverRegion && (
              <>
                <span className="text-white/20">|</span>
                <span>REGION: <span className="text-[#F1F5F9]">{hoverRegion.name}</span></span>
                <span>CROP: <span className="text-[#F59E0B]">{hoverRegion.primary_crop}</span></span>
                <span>STRESS: <span className={hoverRegion.stress_score > 70 ? 'text-[#EF4444]' : hoverRegion.stress_score > 40 ? 'text-[#F59E0B]' : 'text-[#10B981]'}>{hoverRegion.stress_score}</span></span>
              </>
            )}
          </>
        ) : (
          <>
            <span className="text-[#00D4AA]">◌</span>
            <span>TERRALEND ENGINE v1.0</span>
            <span className="text-white/20">|</span>
            <span>MOVE CURSOR OVER MAP FOR COORDINATES</span>
            {selectedRegion && (
              <>
                <span className="text-white/20">|</span>
                <span>ACTIVE: <span className="text-[#00D4AA]">{selectedRegion.name.toUpperCase()}</span></span>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TerraMap;