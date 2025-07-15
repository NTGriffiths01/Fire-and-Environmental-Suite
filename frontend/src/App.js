import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      getCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const getCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Icons
const DashboardIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v1H8V5z" />
  </svg>
);

const InspectionIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const ReportIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const SettingsIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const UsersIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
  </svg>
);

const ReviewIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const AuditIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

// DOC Logo Component
const DOCLogo = ({ size = "w-8 h-8" }) => (
  <div className={`${size} relative`}>
    <div className="absolute inset-0 bg-gradient-to-br from-blue-900 to-blue-800 rounded-full"></div>
    <div className="absolute inset-1 bg-white rounded-full flex items-center justify-center">
      <div className="text-center">
        <div className="w-3 h-4 bg-orange-500 rounded-full mx-auto mb-0.5"></div>
        <div className="text-xs font-bold text-blue-900 leading-none">DOC</div>
      </div>
    </div>
  </div>
);

// Login Component
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const success = await login(email, password);
    if (!success) {
      setError('Invalid email or password');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <DOCLogo size="w-20 h-20" />
          <h2 className="mt-6 text-3xl font-bold text-white">
            Massachusetts Department of Correction
          </h2>
          <p className="mt-2 text-lg text-blue-100">Fire and Environmental Safety Suite</p>
          <div className="mt-4 h-1 w-32 bg-gradient-to-r from-yellow-400 to-yellow-600 mx-auto rounded-full"></div>
        </div>

        <form className="mt-8 space-y-6 bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 shadow-2xl" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-white mb-2">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-blue-200 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-white mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-blue-200 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-blue-900 font-bold py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg transform hover:scale-105"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="text-center">
            <p className="text-blue-200 text-sm">
              Default credentials: admin@madoc.gov / admin123
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ activeTab, setActiveTab, user }) => {
  const getMenuItems = () => {
    const baseItems = [
      { id: 'dashboard', label: 'Dashboard', icon: DashboardIcon }
    ];

    if (user.role === 'admin') {
      return [
        ...baseItems,
        { id: 'inspections', label: 'All Inspections', icon: InspectionIcon },
        { id: 'templates', label: 'Templates', icon: SettingsIcon },
        { id: 'users', label: 'User Management', icon: UsersIcon },
        { id: 'audit', label: 'Audit Logs', icon: AuditIcon },
        { id: 'reports', label: 'Reports', icon: ReportIcon }
      ];
    } else if (user.role === 'inspector') {
      return [
        ...baseItems,
        { id: 'new-inspection', label: 'New Inspection', icon: InspectionIcon },
        { id: 'my-inspections', label: 'My Inspections', icon: InspectionIcon },
        { id: 'reports', label: 'My Reports', icon: ReportIcon }
      ];
    } else if (user.role === 'deputy_of_operations') {
      return [
        ...baseItems,
        { id: 'review-queue', label: 'Review Queue', icon: ReviewIcon },
        { id: 'inspections', label: 'All Inspections', icon: InspectionIcon },
        { id: 'reports', label: 'Reports', icon: ReportIcon }
      ];
    }
    return baseItems;
  };

  return (
    <nav className="bg-blue-900 text-white w-64 min-h-screen shadow-2xl">
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-8">
          <DOCLogo size="w-10 h-10" />
          <div>
            <h1 className="text-lg font-bold">Fire Safety Suite</h1>
            <p className="text-blue-300 text-sm">Massachusetts DOC</p>
          </div>
        </div>

        <div className="space-y-2">
          {getMenuItems().map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                activeTab === item.id
                  ? 'bg-yellow-500 text-blue-900 font-semibold shadow-lg'
                  : 'text-blue-100 hover:bg-blue-800 hover:text-white'
              }`}
            >
              <item.icon />
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="absolute bottom-0 w-64 p-6 border-t border-blue-800">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-8 h-8 bg-blue-700 rounded-full flex items-center justify-center">
            <span className="text-sm font-bold">{user.full_name.charAt(0)}</span>
          </div>
          <div>
            <p className="text-sm font-medium">{user.full_name}</p>
            <p className="text-xs text-blue-300">{user.role.replace('_', ' ')}</p>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Header Component
const Header = ({ title, subtitle, user, logout }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-blue-900">{title}</h1>
          {subtitle && <p className="text-gray-600">{subtitle}</p>}
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
            <p className="text-xs text-gray-500">{user.role.replace('_', ' ')}</p>
          </div>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
};

// Dashboard Components
const DashboardStats = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Total Users</p>
            <p className="text-3xl font-bold text-blue-600">{stats.total_users || 0}</p>
          </div>
          <UsersIcon />
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-600">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Total Facilities</p>
            <p className="text-3xl font-bold text-green-600">{stats.total_facilities || 0}</p>
          </div>
          <SettingsIcon />
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-600">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Total Inspections</p>
            <p className="text-3xl font-bold text-purple-600">{stats.total_inspections || 0}</p>
          </div>
          <InspectionIcon />
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-600">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Pending Reviews</p>
            <p className="text-3xl font-bold text-orange-600">{stats.pending_reviews || 0}</p>
          </div>
          <ReviewIcon />
        </div>
      </div>
    </div>
  );
};

const DashboardContent = ({ user }) => {
  const [stats, setStats] = useState({});

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <div className="space-y-6">
      <DashboardStats stats={stats} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <div>
                <p className="text-sm font-medium">System initialized</p>
                <p className="text-xs text-gray-500">Welcome to the Fire Safety Suite</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Quick Actions</h3>
          <div className="space-y-2">
            {user.role === 'admin' && (
              <button className="w-full text-left p-3 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors">
                <span className="font-medium">Create New Template</span>
              </button>
            )}
            {user.role === 'inspector' && (
              <button className="w-full text-left p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
                <span className="font-medium">Start New Inspection</span>
              </button>
            )}
            {user.role === 'deputy_of_operations' && (
              <button className="w-full text-left p-3 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors">
                <span className="font-medium">Review Pending Inspections</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const InspectionsContent = () => {
  const [inspections, setInspections] = useState([]);

  useEffect(() => {
    fetchInspections();
  }, []);

  const fetchInspections = async () => {
    try {
      const response = await axios.get(`${API}/inspections`);
      setInspections(response.data);
    } catch (error) {
      console.error('Error fetching inspections:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-blue-900">All Inspections</h3>
          <button className="bg-yellow-500 hover:bg-yellow-600 text-blue-900 px-4 py-2 rounded-lg font-medium">
            New Inspection
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">ID</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Citations</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {inspections.map((inspection) => (
                <tr key={inspection.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm">#{inspection.id.slice(-8)}</td>
                  <td className="py-3 px-4 text-sm">{new Date(inspection.inspection_date).toLocaleDateString()}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      inspection.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                      inspection.status === 'submitted' ? 'bg-blue-100 text-blue-800' :
                      inspection.status === 'approved' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {inspection.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm">{inspection.citations?.length || 0}</td>
                  <td className="py-3 px-4">
                    <button className="text-blue-600 hover:text-blue-800 text-sm mr-2">View</button>
                    <button className="text-green-600 hover:text-green-800 text-sm">Edit</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const TemplatesContent = () => {
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-blue-900">Inspection Templates</h3>
          <button className="bg-yellow-500 hover:bg-yellow-600 text-blue-900 px-4 py-2 rounded-lg font-medium">
            Create Template
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div key={template.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <h4 className="font-semibold text-blue-900 mb-2">{template.name}</h4>
              <p className="text-gray-600 text-sm mb-4">{template.description}</p>
              <div className="flex justify-between items-center">
                <span className={`px-2 py-1 text-xs rounded ${
                  template.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {template.is_active ? 'Active' : 'Inactive'}
                </span>
                <div className="space-x-2">
                  <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                  <button className="text-red-600 hover:text-red-800 text-sm">Delete</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const PlaceholderContent = ({ title }) => (
  <div className="bg-white rounded-lg shadow-md p-6">
    <h3 className="text-lg font-semibold text-blue-900 mb-4">{title}</h3>
    <p className="text-gray-600">This section is coming soon...</p>
  </div>
);

// Main Application Component
const MainApp = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Dashboard';
      case 'inspections': return 'All Inspections';
      case 'new-inspection': return 'New Inspection';
      case 'my-inspections': return 'My Inspections';
      case 'templates': return 'Inspection Templates';
      case 'users': return 'User Management';
      case 'audit': return 'Audit Logs';
      case 'reports': return 'Reports';
      case 'review-queue': return 'Review Queue';
      default: return 'Dashboard';
    }
  };

  const getPageSubtitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'System overview and quick actions';
      case 'inspections': return 'View and manage all inspections';
      case 'new-inspection': return 'Create a new fire safety inspection';
      case 'my-inspections': return 'View your inspection history';
      case 'templates': return 'Manage inspection form templates';
      case 'users': return 'Manage system users and permissions';
      case 'audit': return 'View system audit logs';
      case 'reports': return 'Generate and view reports';
      case 'review-queue': return 'Review and approve inspections';
      default: return '';
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardContent user={user} />;
      case 'inspections':
      case 'my-inspections':
        return <InspectionsContent />;
      case 'templates':
        return <TemplatesContent />;
      case 'new-inspection':
        return <PlaceholderContent title="New Inspection" />;
      case 'users':
        return <PlaceholderContent title="User Management" />;
      case 'audit':
        return <PlaceholderContent title="Audit Logs" />;
      case 'reports':
        return <PlaceholderContent title="Reports" />;
      case 'review-queue':
        return <PlaceholderContent title="Review Queue" />;
      default:
        return <DashboardContent user={user} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} user={user} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title={getPageTitle()} 
          subtitle={getPageSubtitle()} 
          user={user} 
          logout={logout} 
        />
        <main className="flex-1 overflow-y-auto p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900">
        <div className="text-center">
          <DOCLogo size="w-16 h-16" />
          <div className="mt-4 animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto"></div>
          <p className="mt-4 text-white">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {user ? <MainApp /> : <LoginPage />}
    </div>
  );
};

export default App;