import React, { useContext } from 'react';
import FeatureToggleContext from '../contexts/FeatureToggleContext';

const FeatureTogglePage = () => {
  const { flags, updateFlag } = useContext(FeatureToggleContext);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Feature Toggles</h1>
      <ul>
        {Object.keys(flags).map((key) => (
          <li key={key} className="mb-2 flex items-center">
            <span className="flex-grow capitalize">{key}</span>
            <input
              type="checkbox"
              checked={flags[key]}
              onChange={(e) => updateFlag(key, e.target.checked)}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FeatureTogglePage;
