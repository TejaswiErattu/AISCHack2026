import React, { createContext, useState, useEffect, useCallback } from 'react';
import { 
  MOCK_REGIONS, 
  MOCK_CLIMATE, 
  MOCK_FINANCIAL, 
  MOCK_NARRATIVES 
} from '../data/mockData';
import { api } from '../api/client';

export const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // --- UI & Navigation State ---
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [activePanel, setActivePanel] = useState('loan_officer'); // loan_officer | farmer | scientist | simulation
  const [activeOverlays, setActiveOverlays] = useState([]); // ['ndvi', 'soil', 'temp', 'rain']
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(true); // Default to true for hackathon safety

  // --- Data State ---
  const [climateData, setClimateData] = useState(MOCK_CLIMATE);
  const [financialOutputs, setFinancialOutputs] = useState(MOCK_FINANCIAL);
  const [narratives, setNarratives] = useState(MOCK_NARRATIVES);

  // --- Simulation State (Step 15 Logic) ---
  const [simulatorValues, setSimulatorValues] = useState({
    temperature: 0,
    drought: 0,
    rainfall: 0
  });

  // --- Actions & Handlers ---

  // Map Overlay Toggle
  const toggleOverlay = (id) => {
    setActiveOverlays(prev => 
      prev.includes(id) ? prev.filter(o => o !== id) : [...prev, id]
    );
  };

  // Manual Simulator Updates
  const updateSimulator = useCallback(async (key, val) => {
    const newValues = { ...simulatorValues, [key]: val };
    setSimulatorValues(newValues);

    if (selectedRegion) {
      // Trigger simulation update via API or Mock
      const updatedFinancials = await api.simulate({
        region_id: selectedRegion.id,
        ...newValues
      }, setIsDemoMode);
      
      setFinancialOutputs(updatedFinancials);
    }
  }, [simulatorValues, selectedRegion]);

  // Preset Archetype Application
  const applyPreset = useCallback((id) => {
    const presets = {
      dust_bowl: { temperature: 4, drought: 90, rainfall: -70 },
      deluge: { temperature: -1, drought: 5, rainfall: 70 },
      frost: { temperature: -3, drought: 20, rainfall: -20 },
      baseline: { temperature: 0, drought: 0, rainfall: 0 }
    };
    
    const selectedPreset = presets[id] || presets.baseline;
    setSimulatorValues(selectedPreset);
    
    // In a real run, you would trigger the simulation API here for the preset
    if (selectedRegion) {
      updateSimulator('temperature', selectedPreset.temperature);
    }
  }, [selectedRegion, updateSimulator]);

  const resetSimulator = () => applyPreset('baseline');

  // --- Region Data Fetching ---
  useEffect(() => {
    if (!selectedRegion) return;

    const loadRegionData = async () => {
      setIsLoading(true);
      
      // Fetch core data
      const climate = await api.getClimate(selectedRegion.id, setIsDemoMode);
      const financial = await api.getFinancial(selectedRegion.id, setIsDemoMode);
      const narrative = await api.getNarrative(selectedRegion.id, activePanel, setIsDemoMode);

      // 800ms "Theatre" delay for Demo Mode to show skeletons
      if (isDemoMode) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      setClimateData(climate);
      setFinancialOutputs(financial);
      setNarratives(prev => ({ ...prev, [activePanel]: narrative }));
      setIsLoading(false);
    };

    loadRegionData();
  }, [selectedRegion, isDemoMode]); // activePanel removed from deps to prevent re-fetch on tab switch

  const value = {
    // State
    selectedRegion,
    activePanel,
    activeOverlays,
    isLoading,
    isDemoMode,
    climateData,
    financialOutputs,
    narratives,
    simulatorValues,
    
    // Setters/Handlers
    setSelectedRegion,
    setActivePanel,
    toggleOverlay,
    updateSimulator,
    applyPreset,
    resetSimulator,
    setIsDemoMode
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContext;