import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DeficiencyManagement = ({ inspection, onClose }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newDeficiency, setNewDeficiency] = useState({
    area_type: '',
    description: '',
    location: '',
    citation_code: '',
    citation_section: '',
    severity: 'medium',
    corrective_action: '',
    target_completion_date: '',
    violation_code_id: '',
    incident_report_number: '', // Will be auto-generated
    recommendations: '' // Will be auto-generated based on description
  });
  const [recommendations, setRecommendations] = useState([]);
  const [isGeneratingRecommendations, setIsGeneratingRecommendations] = useState(false);
  const queryClient = useQueryClient();

  // Get deficiencies for this inspection
  const { data: deficiencies, isLoading } = useQuery({
    queryKey: ['inspection-deficiencies', inspection.id],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/${inspection.id}/deficiencies`);
      if (!response.ok) throw new Error('Failed to fetch deficiencies');
      return response.json();
    },
  });

  // Get violation codes for dropdown
  const { data: violationCodes } = useQuery({
    queryKey: ['violation-codes'],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/violation-codes`);
      if (!response.ok) throw new Error('Failed to fetch violation codes');
      return response.json();
    },
  });

  // Add deficiency mutation
  const addDeficiencyMutation = useMutation({
    mutationFn: async (data) => {
      const formData = new FormData();
      Object.keys(data).forEach(key => {
        if (data[key]) {
          formData.append(key, data[key]);
        }
      });

      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/${inspection.id}/deficiencies`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add deficiency');
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries(['inspection-deficiencies']);
      setShowAddForm(false);
      setNewDeficiency({
        area_type: '',
        description: '',
        location: '',
        citation_code: '',
        citation_section: '',
        severity: 'medium',
        corrective_action: '',
        target_completion_date: '',
        violation_code_id: ''
      });
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  // Update deficiency status mutation
  const updateDeficiencyMutation = useMutation({
    mutationFn: async (data) => {
      const formData = new FormData();
      formData.append('status', data.status);
      if (data.completed_by) {
        formData.append('completed_by', data.completed_by);
      }

      const response = await fetch(`${BACKEND_URL}/api/deficiencies/${data.deficiency_id}/status`, {
        method: 'PUT',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update deficiency');
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries(['inspection-deficiencies']);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  // Generate incident report number automatically
  const generateIncidentReportNumber = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const timestamp = Date.now().toString().slice(-4); // Last 4 digits of timestamp
    return `IR-${year}${month}${day}-${timestamp}`;
  };

  // Generate recommendations based on description
  const generateRecommendations = async (description, violationCode) => {
    if (!description || description.length < 10) {
      setRecommendations([]);
      return;
    }

    setIsGeneratingRecommendations(true);
    
    try {
      // Create recommendations based on common patterns
      const commonRecommendations = {
        'fire': [
          'Ensure all fire safety equipment is properly maintained and inspected',
          'Conduct immediate fire safety training for all personnel',
          'Review and update fire evacuation procedures',
          'Install additional fire detection equipment if necessary'
        ],
        'exit': [
          'Ensure all emergency exits are clearly marked and unobstructed',
          'Test emergency lighting systems monthly',
          'Conduct emergency evacuation drills regularly',
          'Install backup power for emergency systems'
        ],
        'alarm': [
          'Test fire alarm systems monthly and document results',
          'Ensure alarm systems are audible throughout the facility',
          'Maintain backup power systems for alarms',
          'Train staff on alarm system operation'
        ],
        'sprinkler': [
          'Inspect sprinkler heads for obstructions and damage',
          'Test sprinkler system pressure monthly',
          'Ensure water supply is adequate for system operation',
          'Maintain clear access to sprinkler controls'
        ],
        'extinguisher': [
          'Inspect fire extinguishers monthly and recharge as needed',
          'Ensure extinguishers are properly mounted and accessible',
          'Train staff on proper fire extinguisher use',
          'Replace expired or damaged extinguishers immediately'
        ],
        'water': [
          'Test water quality regularly and document results',
          'Ensure adequate water pressure throughout facility',
          'Maintain plumbing systems to prevent contamination',
          'Install backflow prevention devices where required'
        ],
        'waste': [
          'Implement proper waste segregation procedures',
          'Ensure regular waste collection and disposal',
          'Train staff on hazardous waste handling',
          'Maintain clean storage areas for waste containers'
        ],
        'ventilation': [
          'Inspect and clean ventilation systems regularly',
          'Ensure adequate air exchange rates',
          'Replace filters according to manufacturer specifications',
          'Monitor air quality and adjust systems as needed'
        ],
        'electrical': [
          'Inspect electrical panels and ensure proper labeling',
          'Test GFCI outlets monthly',
          'Ensure electrical panels are accessible and unobstructed',
          'Replace damaged electrical equipment immediately'
        ],
        'pest': [
          'Implement integrated pest management program',
          'Seal entry points to prevent pest infiltration',
          'Remove food sources and standing water',
          'Schedule regular pest control inspections'
        ]
      };

      const desc = description.toLowerCase();
      let suggestedRecommendations = [];

      // Match description with common patterns
      Object.keys(commonRecommendations).forEach(key => {
        if (desc.includes(key)) {
          suggestedRecommendations.push(...commonRecommendations[key]);
        }
      });

      // Add violation code specific recommendations
      if (violationCode) {
        const selectedCode = violationCodes?.find(c => c.id === violationCode);
        if (selectedCode) {
          suggestedRecommendations.push(
            `Ensure compliance with ${selectedCode.code_type} ${selectedCode.code_number}: ${selectedCode.title}`,
            `Review ${selectedCode.code_type} requirements for ${selectedCode.area_category} standards`,
            `Implement corrective actions in accordance with ${selectedCode.code_type} regulations`
          );
        }
      }

      // Remove duplicates and limit to 6 recommendations
      const uniqueRecommendations = [...new Set(suggestedRecommendations)].slice(0, 6);
      setRecommendations(uniqueRecommendations);
      
    } catch (error) {
      console.error('Error generating recommendations:', error);
      setRecommendations([]);
    } finally {
      setIsGeneratingRecommendations(false);
    }
  };

  // Handle description change with recommendation generation
  const handleDescriptionChange = (value) => {
    setNewDeficiency(prev => ({ ...prev, description: value }));
    
    // Debounce recommendation generation
    clearTimeout(window.recommendationTimeout);
    window.recommendationTimeout = setTimeout(() => {
      generateRecommendations(value, newDeficiency.violation_code_id);
    }, 1000);
  };

  // Handle violation code change
  const handleViolationCodeChange = (codeId) => {
    const selectedCode = violationCodes?.find(c => c.id === codeId);
    setNewDeficiency(prev => ({ 
      ...prev, 
      violation_code_id: codeId,
      citation_code: selectedCode?.code_number || '',
      citation_section: selectedCode?.section || ''
    }));
    
    // Regenerate recommendations with new violation code
    if (newDeficiency.description) {
      generateRecommendations(newDeficiency.description, codeId);
    }
  };

  const handleUpdateStatus = (deficiencyId, status) => {
    updateDeficiencyMutation.mutate({
      deficiency_id: deficiencyId,
      status: status,
      completed_by: status === 'resolved' ? 'current_user' : null // TODO: Get from auth context
    });
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'low':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'critical':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open':
        return 'bg-red-100 text-red-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'carried_over':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'low':
        return '🟢';
      case 'medium':
        return '🟡';
      case 'high':
        return '🟠';
      case 'critical':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'open':
        return '🔴';
      case 'in_progress':
        return '🟡';
      case 'resolved':
        return '✅';
      case 'carried_over':
        return '⏭️';
      default:
        return '⚪';
    }
  };

  const groupedViolationCodes = violationCodes ? violationCodes.reduce((acc, code) => {
    if (!acc[code.code_type]) {
      acc[code.code_type] = [];
    }
    acc[code.code_type].push(code);
    return acc;
  }, {}) : {};

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-blue-900">
              Deficiency Management
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Add Deficiency Button */}
          <div className="mb-6">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              {showAddForm ? 'Cancel' : '+ Add Deficiency'}
            </button>
          </div>

          {/* Add Deficiency Form */}
          {showAddForm && (
            <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Deficiency</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Area Type *
                  </label>
                  <select
                    value={newDeficiency.area_type}
                    onChange={(e) => setNewDeficiency(prev => ({ ...prev, area_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select area type...</option>
                    <option value="fire_safety">Fire Safety</option>
                    <option value="environmental_health">Environmental Health</option>
                    <option value="general">General</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    value={newDeficiency.location}
                    onChange={(e) => setNewDeficiency(prev => ({ ...prev, location: e.target.value }))}
                    placeholder="e.g., Block A, Kitchen, Main Hall"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Violation Code
                  </label>
                  <select
                    value={newDeficiency.violation_code_id}
                    onChange={(e) => {
                      const selectedCode = violationCodes?.find(c => c.id === e.target.value);
                      setNewDeficiency(prev => ({ 
                        ...prev, 
                        violation_code_id: e.target.value,
                        citation_code: selectedCode?.code_number || '',
                        citation_section: selectedCode?.section || ''
                      }));
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select violation code...</option>
                    {Object.entries(groupedViolationCodes).map(([codeType, codes]) => (
                      <optgroup key={codeType} label={codeType}>
                        {codes.map(code => (
                          <option key={code.id} value={code.id}>
                            {code.code_number} - {code.title}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Severity
                  </label>
                  <select
                    value={newDeficiency.severity}
                    onChange={(e) => setNewDeficiency(prev => ({ ...prev, severity: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Completion Date
                  </label>
                  <input
                    type="date"
                    value={newDeficiency.target_completion_date}
                    onChange={(e) => setNewDeficiency(prev => ({ ...prev, target_completion_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  value={newDeficiency.description}
                  onChange={(e) => setNewDeficiency(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  placeholder="Describe the deficiency..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Corrective Action
                </label>
                <textarea
                  value={newDeficiency.corrective_action}
                  onChange={(e) => setNewDeficiency(prev => ({ ...prev, corrective_action: e.target.value }))}
                  rows={3}
                  placeholder="Describe the corrective action required..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="mt-4 flex justify-end space-x-2">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddDeficiency}
                  disabled={addDeficiencyMutation.isLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {addDeficiencyMutation.isLoading ? 'Adding...' : 'Add Deficiency'}
                </button>
              </div>
            </div>
          )}

          {/* Deficiencies List */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Deficiencies ({deficiencies?.length || 0})
            </h3>

            {isLoading ? (
              <div className="flex justify-center items-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900"></div>
                <span className="ml-2 text-gray-600">Loading deficiencies...</span>
              </div>
            ) : deficiencies && deficiencies.length > 0 ? (
              <div className="space-y-4">
                {deficiencies.map((deficiency) => (
                  <div key={deficiency.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{getSeverityIcon(deficiency.severity)}</span>
                        <div>
                          <div className="font-medium text-gray-900">{deficiency.description}</div>
                          <div className="text-sm text-gray-600">
                            {deficiency.area_type.replace('_', ' ')} • {deficiency.location}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(deficiency.severity)}`}>
                          {deficiency.severity}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(deficiency.status)}`}>
                          {getStatusIcon(deficiency.status)} {deficiency.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>

                    {deficiency.citation_code && (
                      <div className="mb-3">
                        <span className="text-sm font-medium text-gray-700">Citation: </span>
                        <span className="text-sm text-gray-600">{deficiency.citation_code}</span>
                        {deficiency.citation_section && (
                          <span className="text-sm text-gray-600"> - {deficiency.citation_section}</span>
                        )}
                      </div>
                    )}

                    {deficiency.corrective_action && (
                      <div className="mb-3">
                        <span className="text-sm font-medium text-gray-700">Corrective Action: </span>
                        <span className="text-sm text-gray-600">{deficiency.corrective_action}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-500">
                        {deficiency.target_completion_date && (
                          <span>Target: {new Date(deficiency.target_completion_date).toLocaleDateString()}</span>
                        )}
                        {deficiency.carryover_from_month && (
                          <span className="ml-4 text-blue-600">
                            📅 Carried over from month {deficiency.carryover_from_month}
                          </span>
                        )}
                      </div>
                      
                      {deficiency.status !== 'resolved' && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleUpdateStatus(deficiency.id, 'in_progress')}
                            disabled={updateDeficiencyMutation.isLoading}
                            className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 disabled:opacity-50"
                          >
                            In Progress
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(deficiency.id, 'resolved')}
                            disabled={updateDeficiencyMutation.isLoading}
                            className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-md hover:bg-green-200 disabled:opacity-50"
                          >
                            Resolve
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">✅</div>
                <p>No deficiencies found</p>
                <p className="text-sm">This inspection has no recorded deficiencies</p>
              </div>
            )}
          </div>

          {/* Close Button */}
          <div className="flex justify-end mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeficiencyManagement;