import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import InspectionForm from './InspectionForm';
import DigitalSignature from './DigitalSignature';
import DeficiencyManagement from './DeficiencyManagement';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const MonthlyInspectionDashboard = () => {
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedInspection, setSelectedInspection] = useState(null);
  const [activeModal, setActiveModal] = useState(null); // 'create', 'view', 'deficiency'
  const queryClient = useQueryClient();

  // Get available facilities
  const { data: facilities } = useQuery({
    queryKey: ['facilities'],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/facilities`);
      if (!response.ok) throw new Error('Failed to fetch facilities');
      return response.json();
    },
  });

  // Get monthly inspections for selected facility
  const { data: inspections, isLoading } = useQuery({
    queryKey: ['monthly-inspections', selectedFacility, selectedYear],
    queryFn: async () => {
      if (!selectedFacility) return [];
      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/facility/${selectedFacility}?year=${selectedYear}`);
      if (!response.ok) throw new Error('Failed to fetch inspections');
      return response.json();
    },
    enabled: !!selectedFacility,
  });

  // Get inspection statistics
  const { data: stats } = useQuery({
    queryKey: ['inspection-statistics', selectedFacility, selectedYear],
    queryFn: async () => {
      const url = `${BACKEND_URL}/api/monthly-inspections/statistics?${selectedFacility ? `facility_id=${selectedFacility}&` : ''}year=${selectedYear}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch statistics');
      return response.json();
    },
  });

  // Create inspection mutation
  const createInspectionMutation = useMutation({
    mutationFn: async (data) => {
      const formData = new FormData();
      formData.append('facility_id', data.facility_id);
      formData.append('year', data.year);
      formData.append('month', data.month);
      formData.append('created_by', 'current_user'); // TODO: Get from auth context

      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/create`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create inspection');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Monthly inspection created successfully');
      queryClient.invalidateQueries(['monthly-inspections']);
      queryClient.invalidateQueries(['inspection-statistics']);
      setActiveModal(null);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  // Auto-generate inspections mutation
  const autoGenerateMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append('target_year', selectedYear);
      formData.append('target_month', new Date().getMonth() + 1);

      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/auto-generate`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to auto-generate inspections');
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`Generated ${data.result.created_count} monthly inspections`);
      queryClient.invalidateQueries(['monthly-inspections']);
      queryClient.invalidateQueries(['inspection-statistics']);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'inspector_signed':
        return 'bg-yellow-100 text-yellow-800';
      case 'deputy_signed':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'draft':
        return '📝';
      case 'inspector_signed':
        return '✍️';
      case 'deputy_signed':
        return '✅';
      case 'completed':
        return '🎉';
      default:
        return '📄';
    }
  };

  const getMonthName = (monthNumber) => {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[monthNumber - 1];
  };

  const handleCreateInspection = (month) => {
    if (!selectedFacility) {
      toast.error('Please select a facility first');
      return;
    }
    
    createInspectionMutation.mutate({
      facility_id: selectedFacility,
      year: selectedYear,
      month: month,
    });
  };

  const handleViewInspection = (inspection) => {
    setSelectedInspection(inspection);
    setActiveModal('view');
  };

  const closeModal = () => {
    setActiveModal(null);
    setSelectedInspection(null);
  };

  const facilityName = facilities?.find(f => f.id === selectedFacility)?.name || 'All Facilities';

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-blue-900 mb-2">
                Monthly Inspection System
              </h1>
              <p className="text-gray-600">
                Comprehensive monthly inspections with electronic signatures and deficiency tracking
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Facility Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Facility
                </label>
                <select
                  value={selectedFacility || ''}
                  onChange={(e) => setSelectedFacility(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a facility...</option>
                  {facilities?.map((facility) => (
                    <option key={facility.id} value={facility.id}>
                      {facility.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Year Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Year
                </label>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                  className="border border-gray-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i).map(year => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>

              {/* Auto-generate Button */}
              <div className="flex items-end">
                <button
                  onClick={() => autoGenerateMutation.mutate()}
                  disabled={autoGenerateMutation.isLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {autoGenerateMutation.isLoading ? 'Generating...' : '🔄 Auto-Generate'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics Panel */}
        {stats && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Inspection Statistics - {facilityName}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-800">{stats.total_inspections}</div>
                <div className="text-sm text-blue-600">Total Inspections</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-800">{stats.completed_inspections}</div>
                <div className="text-sm text-green-600">Completed</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-800">{stats.pending_inspector}</div>
                <div className="text-sm text-yellow-600">Pending Inspector</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-800">{stats.pending_deputy}</div>
                <div className="text-sm text-red-600">Pending Deputy</div>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-lg font-bold text-purple-800">{stats.completion_rate.toFixed(1)}%</div>
                <div className="text-sm text-purple-600">Completion Rate</div>
              </div>
              <div className="text-center p-4 bg-indigo-50 rounded-lg">
                <div className="text-lg font-bold text-indigo-800">{stats.deficiency_resolution_rate.toFixed(1)}%</div>
                <div className="text-sm text-indigo-600">Deficiency Resolution Rate</div>
              </div>
            </div>
          </div>
        )}

        {/* Monthly Inspections Grid */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Monthly Inspections - {selectedYear}
            </h2>
            {selectedFacility && (
              <p className="text-sm text-gray-600">
                Facility: {facilityName}
              </p>
            )}
          </div>

          {isLoading ? (
            <div className="flex justify-center items-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900"></div>
              <span className="ml-2 text-gray-600">Loading inspections...</span>
            </div>
          ) : selectedFacility ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
                const inspection = inspections?.find(i => i.month === month);
                
                return (
                  <div
                    key={month}
                    className={`border rounded-lg p-4 transition-all duration-200 ${
                      inspection 
                        ? 'bg-white border-blue-200 shadow-sm hover:shadow-md cursor-pointer'
                        : 'bg-gray-50 border-gray-200 border-dashed'
                    }`}
                    onClick={() => inspection ? handleViewInspection(inspection) : handleCreateInspection(month)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">
                        {getMonthName(month)}
                      </h3>
                      {inspection && (
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(inspection.status)}`}>
                          {getStatusIcon(inspection.status)}
                        </span>
                      )}
                    </div>
                    
                    {inspection ? (
                      <div className="space-y-2">
                        <div className="text-sm text-gray-600">
                          Status: <span className="font-medium">{inspection.status.replace('_', ' ')}</span>
                        </div>
                        {inspection.inspection_date && (
                          <div className="text-sm text-gray-600">
                            Date: {new Date(inspection.inspection_date).toLocaleDateString()}
                          </div>
                        )}
                        <div className="text-sm text-gray-600">
                          Created: {new Date(inspection.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <div className="text-2xl mb-2">➕</div>
                        <div className="text-sm text-gray-500">Click to create inspection</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🏢</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Facility</h3>
              <p className="text-gray-600">Choose a facility to view its monthly inspections</p>
            </div>
          )}
        </div>

        {/* Inspection Modal */}
        {selectedInspection && activeModal === 'view' && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-2xl font-bold text-blue-900">
                    {getMonthName(selectedInspection.month)} {selectedInspection.year} Inspection
                  </h3>
                  <button
                    onClick={closeModal}
                    className="text-gray-500 hover:text-gray-700 text-2xl"
                  >
                    ×
                  </button>
                </div>

                <div className="mb-6">
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedInspection.status)}`}>
                      {getStatusIcon(selectedInspection.status)} {selectedInspection.status.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-600">
                      Created by: {selectedInspection.created_by}
                    </span>
                    <span className="text-sm text-gray-600">
                      {new Date(selectedInspection.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">Inspection Details</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Facility:</span>
                        <span className="font-medium">{facilityName}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Month:</span>
                        <span className="font-medium">{getMonthName(selectedInspection.month)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Year:</span>
                        <span className="font-medium">{selectedInspection.year}</span>
                      </div>
                      {selectedInspection.inspection_date && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Inspection Date:</span>
                          <span className="font-medium">{new Date(selectedInspection.inspection_date).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">Actions</h4>
                    <div className="space-y-2">
                      <button
                        onClick={() => setActiveModal('form')}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      >
                        📝 Edit Inspection Form
                      </button>
                      <button
                        onClick={() => setActiveModal('deficiency')}
                        className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                      >
                        ⚠️ Manage Deficiencies
                      </button>
                      <button
                        onClick={() => setActiveModal('signature')}
                        className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                      >
                        ✍️ Digital Signatures
                      </button>
                    </div>
                  </div>
                </div>

                {/* Carryover Deficiencies */}
                {selectedInspection.carryover_deficiencies && selectedInspection.carryover_deficiencies.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">
                      Carryover Deficiencies from Previous Month
                    </h4>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="space-y-2">
                        {selectedInspection.carryover_deficiencies.map((deficiency, index) => (
                          <div key={index} className="flex items-start space-x-2">
                            <span className="text-yellow-600 text-sm">⚠️</span>
                            <div className="flex-1">
                              <div className="text-sm font-medium text-yellow-900">
                                {deficiency.description}
                              </div>
                              <div className="text-xs text-yellow-700">
                                {deficiency.location} • {deficiency.citation_code}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MonthlyInspectionDashboard;