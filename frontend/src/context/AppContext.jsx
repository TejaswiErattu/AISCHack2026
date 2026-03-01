import React, { createContext, useState, useEffect, useCallback, useRef } from 'react';
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
  const [regions, setRegions] = useState(MOCK_REGIONS);
  const [climateData, setClimateData] = useState(MOCK_CLIMATE);
  const [financialOutputs, setFinancialOutputs] = useState(MOCK_FINANCIAL);
  const [narratives, setNarratives] = useState(MOCK_NARRATIVES);

  // --- Simulation State ---
  const [simulatorValues, setSimulatorValues] = useState({
    temperature: 0,
    drought: 0,
    rainfall: 0
  });

  // Debounce ref for simulator updates
  const debounceRef = useRef(null);

  // --- Fetch regions on mount ---
  useEffect(() => {
    const loadRegions = async () => {
      const data = await api.getRegions(setIsDemoMode);
      // Transform region_id → id for frontend compatibility
      const transformed = data.map(r => ({
        ...r,
        id: r.region_id || r.id,
      }));
      setRegions(transformed);
    };
    loadRegions();
  }, []);

  // --- Actions & Handlers ---

  // Map Overlay Toggle
  const toggleOverlay = (id) => {
    setActiveOverlays(prev =>
      prev.includes(id) ? prev.filter(o => o !== id) : [...prev, id]
    );
  };

  // Manual Simulator Updates (debounced)
  const updateSimulator = useCallback(async (key, val) => {
    const newValues = { ...simulatorValues, [key]: val };
    setSimulatorValues(newValues);

    if (!selectedRegion) return;

    // Debounce: cancel previous pending call
    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      const result = await api.simulate({
        region_id: selectedRegion.region_id || selectedRegion.id,
        ...newValues
      }, setIsDemoMode);

      // Handle real API response shape: {baseline, simulated, stress_score, ...}
      if (result && result.simulated) {
        setFinancialOutputs(result.simulated);
        setClimateData(prev => ({
          ...prev,
          yield_stress_score: result.stress_score ?? prev.yield_stress_score,
        }));
      } else {
        // Mock fallback: result is already a flat financial object
        setFinancialOutputs(result);
      }
    }, 300);
  }, [simulatorValues, selectedRegion]);

  // Preset Archetype Application
  const applyPreset = useCallback(async (id) => {
    const presets = {
      dust_bowl: { temperature: 4, drought: 90, rainfall: -70 },
      deluge: { temperature: -1, drought: 5, rainfall: 70 },
      frost: { temperature: -3, drought: 20, rainfall: -20 },
      baseline: { temperature: 0, drought: 0, rainfall: 0 }
    };

    const selectedPreset = presets[id] || presets.baseline;
    setSimulatorValues(selectedPreset);

    if (!selectedRegion) return;

    // Send all preset values in a single simulate call
    const result = await api.simulate({
      region_id: selectedRegion.region_id || selectedRegion.id,
      ...selectedPreset
    }, setIsDemoMode);

    if (result && result.simulated) {
      setFinancialOutputs(result.simulated);
      setClimateData(prev => ({
        ...prev,
        yield_stress_score: result.stress_score ?? prev.yield_stress_score,
      }));
    } else {
      setFinancialOutputs(result);
    }
  }, [selectedRegion]);

  const resetSimulator = () => applyPreset('baseline');

  // --- Region Data Fetching ---
  useEffect(() => {
    if (!selectedRegion) return;

    const loadRegionData = async () => {
      setIsLoading(true);

      const regionId = selectedRegion.region_id || selectedRegion.id;

      // Fetch core data
      const climate = await api.getClimate(regionId, setIsDemoMode);
      const financial = await api.getFinancial(regionId, setIsDemoMode);
      const narrativeResult = await api.getNarrative(regionId, activePanel, setIsDemoMode);

      // Unwrap narrative: backend returns {panel, narrative}, mock returns plain string
      const narrativeText = narrativeResult?.narrative ?? narrativeResult;

      // 800ms "Theatre" delay for Demo Mode to show skeletons
      if (isDemoMode) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      setClimateData(climate);
      setFinancialOutputs(financial);
      setNarratives(prev => ({ ...prev, [activePanel]: narrativeText }));
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
    regions,
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
