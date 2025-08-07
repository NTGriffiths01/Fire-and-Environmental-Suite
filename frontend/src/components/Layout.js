import React, { useContext } from 'react';
import { Link, Outlet } from 'react-router-dom';
import logo from '../logoBase64';
import FeatureToggleContext from '../contexts/FeatureToggleContext';

const Layout = ({ children }) => {
  const { flags } = useContext(FeatureToggleContext);

  const navItems = [
    { to: '/monthly-inspections', label: 'Monthly Inspections', flag: true },
    { to: '/weekly-inspections', label: 'Weekly Inspections', flag: flags.weeklyInspections },
    { to: '/fire-watch-logs', label: 'Fire Watch Logs', flag: flags.fireWatchLogs },
    { to: '/functional-testing', label: 'Functional Testing', flag: flags.functionalTesting },
    { to: '/hot-work-permits', label: 'Hot Work Permits', flag: flags.hotWorkPermit },
    { to: '/evacuation-maps', label: 'Evacuation Maps & Drills', flag: flags.evacuationMaps },
    { to: '/plan-of-action', label: 'Plan of Action', flag: flags.planOfAction },
    { to: '/chemical-inventory', label: 'Chemical & Equipment', flag: flags.chemicalInventory },
    { to: '/environmental-inspections', label: 'Env Health Inspections', flag: flags.housekeeping || flags.pestControl || flags.personalHygiene || flags.hairCare },
    { to: '/housekeeping', label: 'Housekeeping', flag: flags.housekeeping },
    { to: '/pest-control', label: 'Pest Control', flag: flags.pestControl },
    { to: '/personal-hygiene', label: 'Personal Hygiene & Razor', flag: flags.personalHygiene },
    { to: '/hair-care', label: 'Hair Care', flag: flags.hairCare },
    { to: '/heat-measures', label: 'Heat Measures', flag: flags.heatMeasures },
    { to: '/training-modules', label: 'Training Modules', flag: flags.trainingModules },
    { to: '/waste-disposal', label: 'Waste Disposal & Recycling', flag: flags.wasteDisposal },
    { to: '/razor-tracking', label: 'Razor Tracking', flag: flags.razorTracking },
    { to: '/dashboards', label: 'Dashboards', flag: flags.dashboards },
  ];

  return (
    <div className="flex h-screen">
      <aside className="w-60 bg-gray-100 p-4 overflow-y-auto">
        <div className="flex items-center mb-6">
          <img src={logo} alt="Mass DOC Fire Safety" className="h-10 mr-2" />
          <span className="font-bold text-lg">Fire Safety & EHS</span>
        </div>
        <nav>
          {navItems.filter(item => item.flag).map((item) => (
            <Link key={item.to} to={item.to} className="block py-2 px-2 rounded hover:bg-gray-200">
              {item.label}
            </Link>
          ))}
          <div className="mt-4 border-t pt-4">
            <Link to="/admin/feature-toggles" className="block py-2 px-2 rounded hover:bg-gray-200">
              Admin: Feature Toggles
            </Link>
          </div>
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto">
        {children || <Outlet />}
      </main>
    </div>
  );
};

export default Layout;
