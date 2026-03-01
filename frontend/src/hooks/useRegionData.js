import { useState, useEffect, useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { api } from '../api/client';

export const useRegionData = (regionId) => {
  const { setClimateData, setFinancialOutputs, setNarratives, isDemoMode, setIsDemoMode } = useContext(AppContext);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!regionId) return;

    const fetchData = async () => {
      setIsLoading(true);

      // Execute API calls
      const [climate, financial, narrative] = await Promise.all([
        api.getClimate(regionId, setIsDemoMode),
        api.getFinancial(regionId, setIsDemoMode),
        api.getNarrative(regionId, 'loan_officer', setIsDemoMode)
      ]);

      // Apply the 800ms "Theatre" delay if in Demo Mode
      if (isDemoMode) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      setClimateData(climate);
      setFinancialOutputs(financial);
      setNarratives(prev => ({ ...prev, loan_officer: narrative }));
      setIsLoading(false);
    };

    fetchData();
  }, [regionId]);

  return { isLoading };
};