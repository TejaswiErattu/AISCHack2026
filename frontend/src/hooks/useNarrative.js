import { useState, useCallback, useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { api } from '../api/client';

/**
 * useNarrative Hook
 * Manages fetching and local caching of persona-specific AI narratives.
 *
 */
const useNarrative = () => {
  const { 
    selectedRegion, 
    narratives, 
    setNarratives, 
    setIsDemoMode 
  } = useContext(AppContext);
  
  const [isNarrativeLoading, setIsNarrativeLoading] = useState(false);

  const fetchNarrative = useCallback(async (panelId) => {
    // Return early if narrative for this panel is already cached
    if (narratives[panelId] || !selectedRegion) return;

    setIsNarrativeLoading(true);
    try {
      const result = await api.getNarrative(
        selectedRegion.id, 
        panelId, 
        setIsDemoMode
      );
      
      setNarratives(prev => ({
        ...prev,
        [panelId]: result
      }));
    } catch (err) {
      console.error("Narrative fetch failed:", err);
    } finally {
      setIsNarrativeLoading(false);
    }
  }, [selectedRegion, narratives, setNarratives, setIsDemoMode]);

  return { fetchNarrative, isNarrativeLoading };
};

export default useNarrative;