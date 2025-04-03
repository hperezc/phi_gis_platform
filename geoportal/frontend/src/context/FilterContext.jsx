import { createContext, useContext, useState } from 'react';

const FilterContext = createContext();

export function FilterProvider({ children }) {
  const [lastFilter, setLastFilter] = useState({
    layer: '',
    field: '',
    value: '',
    results: []
  });

  const updateLastFilter = (filter) => {
    setLastFilter(filter);
  };

  return (
    <FilterContext.Provider value={{ lastFilter, updateLastFilter }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilter() {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error('useFilter must be used within a FilterProvider');
  }
  return context;
} 