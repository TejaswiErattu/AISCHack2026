import React, { useContext, useState } from 'react';
import Topbar from './Topbar';
import TerraMap from '../map/TerraMap';
import PanelTabs from '../panels/PanelTabs';
import PanelSwitcher from '../panels/PanelSwitcher';
import ClimateSimulator from '../simulator/ClimateSimulator';
import ComparisonBar from '../comparison/ComparisonBar';
import { AppContext } from '../../context/AppContext';

const AppLayout = () => {
  const { isDemoMode, selectedRegion } = useContext(AppContext);
  const [showPanel, setShowPanel] = useState(false);

  return (
    <div className="flex flex-col h-screen w-full bg-background-primary overflow-hidden font-sans">
      {/* 1. TOPBAR */}
      <div className="flex-none">
        <Topbar />
      </div>

      {/* 2. MAIN CONTENT AREA */}
      <main className="flex flex-col lg:flex-row flex-1 overflow-hidden relative">
        {/* MAP — full width on mobile, 55% on desktop */}
        <section className="w-full lg:w-[55%] h-[50vh] lg:h-full relative border-b lg:border-b-0 lg:border-r border-border">
          <TerraMap />

          {/* Mobile toggle button to show panels */}
          {selectedRegion && (
            <button
              onClick={() => setShowPanel(!showPanel)}
              className="lg:hidden absolute bottom-4 left-1/2 -translate-x-1/2 z-[1000] bg-accent-primary text-background-primary text-xs font-bold uppercase tracking-wider px-4 py-2 rounded-full shadow-glow-teal"
            >
              {showPanel ? '← Back to Map' : 'View Analysis →'}
            </button>
          )}
        </section>

        {/* PANELS — full width on mobile (overlay), 45% on desktop */}
        <section className={`
          w-full lg:w-[45%] h-[50vh] lg:h-full flex flex-col bg-background-secondary relative
          ${showPanel ? 'flex' : 'hidden lg:flex'}
        `}>
          {/* Mobile back button */}
          <button
            onClick={() => setShowPanel(false)}
            className="lg:hidden flex-none p-2 text-xs text-accent-primary font-bold uppercase border-b border-border"
          >
            ← Back to Map
          </button>

          <div className="flex-none z-20">
            <PanelTabs />
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-3 sm:p-4 lg:p-6">
            <PanelSwitcher />
          </div>
        </section>
      </main>

      {/* 3. FOOTER (Comparison + Simulator) */}
      <footer className="flex-none flex flex-col z-[3000] shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
        <ComparisonBar />
        <div className="h-auto lg:h-[140px] bg-background-secondary">
          <ClimateSimulator />
        </div>
      </footer>
    </div>
  );
};

export default AppLayout;