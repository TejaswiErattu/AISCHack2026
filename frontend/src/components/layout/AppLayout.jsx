import React, { useContext } from 'react';
import Topbar from './Topbar';
import TerraMap from '../map/TerraMap';
import PanelTabs from '../panels/PanelTabs';
import PanelSwitcher from '../panels/PanelSwitcher';
import ClimateSimulator from '../simulator/ClimateSimulator';
import ComparisonBar from '../comparison/ComparisonBar';
import { AppContext } from '../../context/AppContext';

const AppLayout = () => {
  const { isDemoMode, selectedRegion } = useContext(AppContext);

  return (
    <div className="flex flex-col h-screen w-full bg-background-primary overflow-hidden font-sans">
      {/* 1. TOPBAR (Fixed 56px) */}
      <div className="flex-none">
        <Topbar />
      </div>

      {/* 2. MAIN CONTENT AREA (Map & Panels) */}
      <main className="flex flex-1 overflow-hidden">
        {/* LEFT COLUMN: 55% MAP */}
        <section className="w-[55%] h-full relative border-r border-border">
          <TerraMap />
        </section>

        {/* RIGHT COLUMN: 45% PANELS */}
        <section className="w-[45%] h-full flex flex-col bg-background-secondary relative">
          {/* Panel Navigation (Sticky at top of this column) */}
          <div className="flex-none z-20">
            <PanelTabs />
          </div>

          {/* Independent Scroll Area for Panel Content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
            <PanelSwitcher />
          </div>
        </section>
      </main>

      {/* 3. FOOTER STACK (Comparison + Simulator) */}
      <footer className="flex-none flex flex-col z-[3000] shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
        {/* Comparison Bar (Height 32px-88px) */}
        <ComparisonBar />
        
        {/* Climate Shock Simulator (Fixed 140px) */}
        <div className="h-[140px] bg-background-secondary">
          <ClimateSimulator />
        </div>
      </footer>
    </div>
  );
};

export default AppLayout;