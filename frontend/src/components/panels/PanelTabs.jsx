import React, { useContext } from 'react';
import { AppContext } from '../../context/AppContext';

const TABS = [
  { id: 'loan_officer', label: 'Loan Officer', icon: '💼' },
  { id: 'farmer', label: 'Farmer', icon: '🚜' },
  { id: 'simulation', label: 'Simulation Lab', icon: '⚡', isSpecial: true },
];

const PanelTabs = () => {
  const { activePanel, setActivePanel } = useContext(AppContext);

  return (
    <div className="w-full p-4 border-b border-border bg-background-secondary/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex p-1 bg-background-card rounded-xl border border-border gap-1">
        {TABS.map((tab) => {
          const isActive = activePanel === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => setActivePanel(tab.id)}
              className={`
                relative flex-1 flex items-center justify-center gap-2 py-2 rounded-lg
                text-[12px] font-bold uppercase tracking-wider transition-all duration-200
                ${isActive 
                  ? 'text-text-primary shadow-glow-teal border border-accent-primary/50' 
                  : 'text-text-muted hover:text-text-secondary'}
                ${isActive && !tab.isSpecial ? 'bg-background-elevated' : ''}
                ${isActive && tab.isSpecial ? 'bg-gradient-to-r from-purple-900/40 to-accent-primary/20 border-purple-500/50' : ''}
              `}
            >
              <span className="text-[14px]">{tab.icon}</span>
              {tab.label}
              
              {/* Linear-style active indicator line (optional enhancement) */}
              {isActive && (
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1/2 h-[2px] bg-accent-primary rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default PanelTabs;