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

// DOC Logo Component
const DOCLogo = () => (
  <div className="flex items-center justify-center w-24 h-24 bg-white rounded-full p-2 shadow-lg">
    <div className="relative w-full h-full">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 rounded-full"></div>
      <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-orange-500 rounded-full mx-auto mb-1 flex items-center justify-center">
            <div className="w-3 h-5 bg-orange-600 rounded-sm"></div>
          </div>
          <div className="text-xs font-bold text-blue-900">FIRE</div>
          <div className="text-xs font-bold text-blue-900">SAFETY</div>
        </div>
      </div>
      <div className="absolute -top-1 -left-1 -right-1 -bottom-1 border-4 border-gold-500 rounded-full"></div>
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
          <DOCLogo />
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

// Dynamic Inspection Form Component
const InspectionFormRenderer = ({ template, onSubmit, onDraft, initialData = {} }) => {
  const [formData, setFormData] = useState(initialData.form_data || {});
  const [attachments, setAttachments] = useState(initialData.attachments || []);
  const [citations, setCitations] = useState(initialData.citations || []);
  const [citationSuggestions, setCitationSuggestions] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formDataUpload = new FormData();
    formDataUpload.append('file', file);

    try {
      const response = await axios.post(`${API}/upload`, formDataUpload, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setAttachments(prev => [...prev, {
        id: response.data.file_id,
        filename: response.data.filename,
        url: response.data.file_id
      }]);
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const suggestCitations = async (finding) => {
    if (!finding || finding.length < 10) return;
    
    try {
      const response = await axios.post(`${API}/citations/suggest`, { finding });
      setCitationSuggestions(response.data.suggestions);
    } catch (error) {
      console.error('Error getting citation suggestions:', error);
    }
  };

  const addCitation = (suggestion) => {
    setCitations(prev => [...prev, {
      id: Date.now().toString(),
      ...suggestion,
      applied_to: 'inspection'
    }]);
    setCitationSuggestions([]);
  };

  const removeCitation = (citationId) => {
    setCitations(prev => prev.filter(c => c.id !== citationId));
  };

  const handleSubmit = async (status) => {
    setIsSubmitting(true);
    const submissionData = {
      template_id: template.id,
      form_data: formData,
      attachments: attachments.map(a => a.id),
      citations,
      status
    };

    try {
      if (status === 'draft') {
        await onDraft(submissionData);
      } else {
        await onSubmit(submissionData);
      }
    } catch (error) {
      console.error('Error submitting form:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderField = (field, sectionIndex, fieldIndex) => {
    const fieldName = `${sectionIndex}_${fieldIndex}_${field.name}`;
    const value = formData[fieldName] || '';

    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            className="form-input"
            value={value}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            placeholder={field.placeholder}
          />
        );
      case 'textarea':
        return (
          <div>
            <textarea
              className="form-input min-h-[100px]"
              value={value}
              onChange={(e) => handleFieldChange(fieldName, e.target.value)}
              placeholder={field.placeholder}
              onBlur={() => suggestCitations(value)}
            />
            {citationSuggestions.length > 0 && (
              <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-semibold text-blue-900 mb-2">Suggested Citations:</p>
                {citationSuggestions.map((suggestion, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-white p-2 rounded border mb-1">
                    <div>
                      <span className="font-medium">{suggestion.code}</span>
                      <span className="text-gray-600 ml-2">{suggestion.title}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => addCitation(suggestion)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Add
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case 'checkbox':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={value === true}
              onChange={(e) => handleFieldChange(fieldName, e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Yes</span>
          </div>
        );
      case 'select':
        return (
          <select
            className="form-input"
            value={value}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          >
            <option value="">Select...</option>
            {field.options?.map((option, idx) => (
              <option key={idx} value={option.value}>{option.label}</option>
            ))}
          </select>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
      <div className="flex items-center mb-6">
        <DOCLogo />
        <div className="ml-4">
          <h2 className="text-2xl font-bold text-blue-900">{template.name}</h2>
          <p className="text-gray-600">{template.description}</p>
        </div>
      </div>

      <form className="space-y-6">
        {template.template_data.sections?.map((section, sectionIndex) => (
          <div key={sectionIndex} className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4 border-b border-gray-200 pb-2">
              {section.title}
            </h3>
            <div className="space-y-4">
              {section.fields?.map((field, fieldIndex) => (
                <div key={fieldIndex} className="form-group">
                  <label className="form-label">{field.label}</label>
                  {renderField(field, sectionIndex, fieldIndex)}
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* File Attachments */}
        <div className="border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Attachments</h3>
          <input
            type="file"
            onChange={handleFileUpload}
            className="form-input"
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
          />
          {attachments.length > 0 && (
            <div className="mt-4 space-y-2">
              {attachments.map((attachment, idx) => (
                <div key={idx} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                  <span className="text-sm">{attachment.filename}</span>
                  <button
                    type="button"
                    onClick={() => setAttachments(prev => prev.filter((_, i) => i !== idx))}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Applied Citations */}
        {citations.length > 0 && (
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">Applied Citations</h3>
            <div className="space-y-2">
              {citations.map((citation) => (
                <div key={citation.id} className="flex items-center justify-between bg-red-50 p-3 rounded border border-red-200">
                  <div>
                    <span className="font-medium text-red-900">{citation.code}</span>
                    <span className="text-red-700 ml-2">{citation.title}</span>
                    <p className="text-sm text-red-600">{citation.description}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCitation(citation.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <button
            type="button"
            onClick={() => handleSubmit('draft')}
            disabled={isSubmitting}
            className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:opacity-50"
          >
            Save as Draft
          </button>
          <button
            type="button"
            onClick={() => handleSubmit('submitted')}
            disabled={isSubmitting}
            className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-yellow-600 text-blue-900 font-bold rounded-lg hover:from-yellow-600 hover:to-yellow-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Submitting...' : 'Submit for Review'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Inspection Review Component
const InspectionReview = ({ inspection, onReview, onClose }) => {
  const [comments, setComments] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleReview = async (action) => {
    setIsProcessing(true);
    try {
      await onReview(inspection.id, action, comments);
      onClose();
    } catch (error) {
      console.error('Error reviewing inspection:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const generatePDF = async () => {
    try {
      const response = await axios.get(`${API}/inspections/${inspection.id}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `inspection_${inspection.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center">
            <DOCLogo />
            <div className="ml-4">
              <h3 className="text-2xl font-bold text-blue-900">Inspection Review</h3>
              <p className="text-gray-600">ID: {inspection.id}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
        </div>

        <div className="space-y-6">
          {/* Inspection Details */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Inspection Details</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Date:</span>
                <p>{new Date(inspection.inspection_date).toLocaleDateString()}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Status:</span>
                <p className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                  inspection.status === 'submitted' ? 'bg-blue-100 text-blue-800' : 
                  inspection.status === 'approved' ? 'bg-green-100 text-green-800' : 
                  'bg-red-100 text-red-800'
                }`}>
                  {inspection.status}
                </p>
              </div>
            </div>
          </div>

          {/* Form Data */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Form Data</h4>
            <div className="space-y-2">
              {Object.entries(inspection.form_data || {}).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-sm text-gray-600">{key}:</span>
                  <span className="text-sm">{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Citations */}
          {inspection.citations && inspection.citations.length > 0 && (
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <h4 className="font-semibold text-red-900 mb-2">Citations</h4>
              <div className="space-y-2">
                {inspection.citations.map((citation, idx) => (
                  <div key={idx} className="bg-white p-3 rounded border">
                    <div className="font-medium text-red-900">{citation.code}</div>
                    <div className="text-red-700">{citation.title}</div>
                    <div className="text-sm text-red-600">{citation.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Comments */}
          <div>
            <label className="form-label">Review Comments</label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="form-input min-h-[100px]"
              placeholder="Enter review comments..."
              required
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between pt-6 border-t">
            <button
              onClick={generatePDF}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Generate PDF
            </button>
            <div className="flex space-x-4">
              <button
                onClick={() => handleReview('reject')}
                disabled={isProcessing || !comments}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {isProcessing ? 'Processing...' : 'Reject'}
              </button>
              <button
                onClick={() => handleReview('approve')}
                disabled={isProcessing || !comments}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {isProcessing ? 'Processing...' : 'Approve'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Components
const AdminDashboard = () => {
  const [stats, setStats] = useState({});
  const [templates, setTemplates] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchTemplates();
    fetchAuditLogs();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const response = await axios.get(`${API}/audit-logs`);
      setAuditLogs(response.data.slice(0, 10)); // Show last 10 logs
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center mb-6">
        <DOCLogo />
        <div className="ml-4">
          <h2 className="text-2xl font-bold text-blue-900">Administration Dashboard</h2>
          <p className="text-gray-600">System management and oversight</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Users</h3>
          <p className="text-3xl font-bold text-blue-600">{stats.total_users || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Facilities</h3>
          <p className="text-3xl font-bold text-green-600">{stats.total_facilities || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Inspections</h3>
          <p className="text-3xl font-bold text-purple-600">{stats.total_inspections || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Pending Reviews</h3>
          <p className="text-3xl font-bold text-orange-600">{stats.pending_reviews || 0}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Templates Management */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-blue-900">Inspection Templates</h3>
            <button
              onClick={() => setShowCreateTemplate(true)}
              className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-blue-900 px-4 py-2 rounded-lg hover:from-yellow-600 hover:to-yellow-700 font-medium"
            >
              Create Template
            </button>
          </div>
          <div className="space-y-3">
            {templates.slice(0, 5).map((template) => (
              <div key={template.id} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900">{template.name}</h4>
                <p className="text-gray-600 text-sm">{template.description}</p>
                <div className="mt-2 flex justify-between items-center">
                  <span className={`px-2 py-1 text-xs rounded ${
                    template.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {template.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <button className="text-blue-600 hover:text-blue-800 text-sm">
                    Edit
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Logs */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Recent Audit Logs</h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {auditLogs.map((log) => (
              <div key={log.id} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{log.action}</p>
                    <p className="text-sm text-gray-600">{log.resource_type}: {log.resource_id}</p>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(log.timestamp).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const InspectorDashboard = () => {
  const [stats, setStats] = useState({});
  const [inspections, setInspections] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [showCreateInspection, setShowCreateInspection] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editingInspection, setEditingInspection] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchInspections();
    fetchTemplates();
    fetchFacilities();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchInspections = async () => {
    try {
      const response = await axios.get(`${API}/inspections`);
      setInspections(response.data);
    } catch (error) {
      console.error('Error fetching inspections:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchFacilities = async () => {
    try {
      const response = await axios.get(`${API}/facilities`);
      setFacilities(response.data);
    } catch (error) {
      console.error('Error fetching facilities:', error);
    }
  };

  const handleCreateInspection = async (formData) => {
    try {
      const inspectionData = {
        ...formData,
        facility_id: facilities[0]?.id, // Default to first facility
        inspection_date: new Date().toISOString()
      };
      
      await axios.post(`${API}/inspections`, inspectionData);
      setShowCreateInspection(false);
      setSelectedTemplate(null);
      fetchInspections();
    } catch (error) {
      console.error('Error creating inspection:', error);
    }
  };

  const handleUpdateInspection = async (formData) => {
    try {
      await axios.put(`${API}/inspections/${editingInspection.id}`, {
        ...editingInspection,
        ...formData
      });
      setEditingInspection(null);
      setSelectedTemplate(null);
      fetchInspections();
    } catch (error) {
      console.error('Error updating inspection:', error);
    }
  };

  const startNewInspection = (template) => {
    setSelectedTemplate(template);
    setShowCreateInspection(true);
  };

  const editInspection = (inspection) => {
    const template = templates.find(t => t.id === inspection.template_id);
    setSelectedTemplate(template);
    setEditingInspection(inspection);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center mb-6">
        <DOCLogo />
        <div className="ml-4">
          <h2 className="text-2xl font-bold text-blue-900">Inspector Dashboard</h2>
          <p className="text-gray-600">Create and manage inspection forms</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">My Inspections</h3>
          <p className="text-3xl font-bold text-blue-600">{stats.my_inspections || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Draft Inspections</h3>
          <p className="text-3xl font-bold text-orange-600">{stats.draft_inspections || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Submitted</h3>
          <p className="text-3xl font-bold text-green-600">{stats.submitted_inspections || 0}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-4">Start New Inspection</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <button
              key={template.id}
              onClick={() => startNewInspection(template)}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left transition-colors"
            >
              <h4 className="font-semibold text-blue-900">{template.name}</h4>
              <p className="text-sm text-gray-600">{template.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Inspections List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-4">My Inspections</h3>
        <div className="space-y-3">
          {inspections.map((inspection) => (
            <div key={inspection.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-blue-900">
                    Inspection #{inspection.id.slice(-8)}
                  </h4>
                  <p className="text-gray-600 text-sm">
                    {new Date(inspection.inspection_date).toLocaleDateString()}
                  </p>
                  <div className="mt-2">
                    <span className={`px-2 py-1 text-xs rounded font-medium ${
                      inspection.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                      inspection.status === 'submitted' ? 'bg-blue-100 text-blue-800' :
                      inspection.status === 'approved' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {inspection.status}
                    </span>
                    {inspection.citations && inspection.citations.length > 0 && (
                      <span className="ml-2 px-2 py-1 text-xs rounded bg-red-100 text-red-800">
                        {inspection.citations.length} Citation(s)
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  {inspection.status === 'draft' && (
                    <button
                      onClick={() => editInspection(inspection)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Edit
                    </button>
                  )}
                  <button className="text-gray-600 hover:text-gray-800 text-sm">
                    View
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form Modal */}
      {(showCreateInspection || editingInspection) && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold text-blue-900">
                {editingInspection ? 'Edit Inspection' : 'New Inspection'}
              </h3>
              <button
                onClick={() => {
                  setShowCreateInspection(false);
                  setEditingInspection(null);
                  setSelectedTemplate(null);
                }}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            <InspectionFormRenderer
              template={selectedTemplate}
              onSubmit={editingInspection ? handleUpdateInspection : handleCreateInspection}
              onDraft={editingInspection ? handleUpdateInspection : handleCreateInspection}
              initialData={editingInspection}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const DeputyDashboard = () => {
  const [stats, setStats] = useState({});
  const [inspections, setInspections] = useState([]);
  const [selectedInspection, setSelectedInspection] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchInspections();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchInspections = async () => {
    try {
      const response = await axios.get(`${API}/inspections`);
      setInspections(response.data);
    } catch (error) {
      console.error('Error fetching inspections:', error);
    }
  };

  const handleReview = async (inspectionId, action, comments) => {
    try {
      await axios.post(`${API}/inspections/${inspectionId}/review`, {
        action,
        comments
      });
      fetchInspections();
    } catch (error) {
      console.error('Error reviewing inspection:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center mb-6">
        <DOCLogo />
        <div className="ml-4">
          <h2 className="text-2xl font-bold text-blue-900">Deputy Operations Dashboard</h2>
          <p className="text-gray-600">Review and approve inspection reports</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Pending Reviews</h3>
          <p className="text-3xl font-bold text-orange-600">{stats.pending_reviews || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Approved</h3>
          <p className="text-3xl font-bold text-green-600">{stats.approved_inspections || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-600">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Rejected</h3>
          <p className="text-3xl font-bold text-red-600">{stats.rejected_inspections || 0}</p>
        </div>
      </div>

      {/* Inspections for Review */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-4">Inspections for Review</h3>
        <div className="space-y-4">
          {inspections.map((inspection) => (
            <div key={inspection.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-blue-900">
                    Inspection #{inspection.id.slice(-8)}
                  </h4>
                  <p className="text-gray-600 text-sm">
                    Date: {new Date(inspection.inspection_date).toLocaleDateString()}
                  </p>
                  <div className="mt-2">
                    <span className={`px-2 py-1 text-xs rounded font-medium ${
                      inspection.status === 'submitted' ? 'bg-blue-100 text-blue-800' :
                      inspection.status === 'approved' ? 'bg-green-100 text-green-800' :
                      inspection.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {inspection.status}
                    </span>
                    {inspection.citations && inspection.citations.length > 0 && (
                      <span className="ml-2 px-2 py-1 text-xs rounded bg-red-100 text-red-800">
                        {inspection.citations.length} Citation(s)
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedInspection(inspection)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    Review
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Review Modal */}
      {selectedInspection && (
        <InspectionReview
          inspection={selectedInspection}
          onReview={handleReview}
          onClose={() => setSelectedInspection(null)}
        />
      )}
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();

  const renderContent = () => {
    switch (user.role) {
      case 'admin':
        return <AdminDashboard />;
      case 'inspector':
        return <InspectorDashboard />;
      case 'deputy_of_operations':
        return <DeputyDashboard />;
      default:
        return <div>Invalid role</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="w-10 h-10 mr-3">
                <DOCLogo />
              </div>
              <div>
                <h1 className="text-xl font-bold text-blue-900">
                  Fire and Environmental Safety Suite
                </h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-700">
                Welcome, {user.full_name}
              </div>
              <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {user.role.replace('_', ' ')}
              </div>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {renderContent()}
        </div>
      </main>
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
          <DOCLogo />
          <div className="mt-4 animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto"></div>
          <p className="mt-4 text-white">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {user ? <Dashboard /> : <LoginPage />}
    </div>
  );
};

export default App;