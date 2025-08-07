import React, { createContext, useState, useEffect } from 'react';
import featureFlags from '../features';

const FeatureToggleContext = createContext({
  flags: featureFlags,
  updateFlag: () => {},
});

export const FeatureToggleProvider = ({ children }) => {
  const [flags, setFlags] = useState(() => {
    const stored = localStorage.getItem('featureFlags');
    return stored ? JSON.parse(stored) : featureFlags;
  });

  const updateFlag = (key, value) => {
    setFlags(prev => {
      const updated = { ...prev, [key]: value };
      localStorage.setItem('featureFlags', JSON.stringify(updated));
      return updated;
    });
  };

  useEffect(() => {
    localStorage.setItem('featureFlags', JSON.stringify(flags));
  }, [flags]);

  return (
    <FeatureToggleContext.Provider value={{ flags, updateFlag }}>
      {children}
    </FeatureToggleContext.Provider>
  );
};

export default FeatureToggleContext;
