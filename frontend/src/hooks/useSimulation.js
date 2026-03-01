import { useState, useCallback, useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { api } from '../api/client';

/**
 * useSimulation Hook
 * Handles the logic for running real-time climate impact simulations.
 *
 */
const useSimulation = () => {
  const { 
    selectedRegion, 
    setFinancialOutputs, 
    setIsDemoMode 
  } = useContext(AppContext);
  
  const [isSimulating, setIsSimulating] = useState(false);

  const runSimulation = useCallback(async (values) => {
    if (!selectedRegion) return;

    setIsSimulating(true);
    try {
      // Sends current slider states to the simulation engine
      const updatedFinancials = await api.simulate({
        region_id: selectedRegion.id,
        temperature: values.temperature,
        drought: values.drought,
        rainfall: values.rainfall
      }, setIsDemoMode);

      setFinancialOutputs(updatedFinancials);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setIsSimulating(false);
    }
  }, [selectedRegion, setFinancialOutputs, setIsDemoMode]);

  return { runSimulation, isSimulating };
};

export default useSimulation;