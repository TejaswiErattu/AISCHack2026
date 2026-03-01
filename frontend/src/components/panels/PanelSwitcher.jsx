import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';
import LoanOfficerPanel from './LoanOfficerPanel';
import FarmerPanel from './FarmerPanel';
import ScientistPanel from './ScientistPanel';
import SimulationLab from './SimulationLab';

const PanelSwitcher = () => {
  const { activePanel, selectedRegion } = useContext(AppContext);

  if (!selectedRegion) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12 text-center animate-pulse">
        <div className="w-16 h-16 border-2 border-dashed border-border rounded-full mb-4 flex items-center justify-center text-2xl opacity-30">
          ←
        </div>
        <h3 className="text-text-secondary font-semibold uppercase tracking-widest text-sm">
          Select a region on the map
        </h3>
        <p className="text-text-muted text-xs mt-2 max-w-[200px]">
          Click a marker to initialize climate-aware lending analysis
        </p>
      </div>
    );
  }

  const renderPanel = () => {
    switch (activePanel) {
      case 'loan_officer': return <LoanOfficerPanel />;
      case 'farmer': return <FarmerPanel />;
      case 'scientist': return <ScientistPanel />;
      case 'simulation': return <SimulationLab />;
      default: return <LoanOfficerPanel />;
    }
  };

  return (
    <div key={activePanel} className="animate-panel-entry">
      {renderPanel()}
    </div>
  );
};

export default PanelSwitcher;