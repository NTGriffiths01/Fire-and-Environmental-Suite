import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const InspectionForm = ({ inspection, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    fire_safety: {
      sprinkler_system: '',
      fire_alarms: '',
      fire_extinguishers: '',
      emergency_exits: '',
      fire_doors: '',
      smoking_areas: '',
      electrical_systems: '',
      kitchen_equipment: '',
      storage_areas: '',
      maintenance_areas: ''
    },
    environmental_health: {
      water_supply: '',
      waste_management: '',
      ventilation: '',
      pest_control: '',
      food_service: '',
      sanitation: '',
      hazardous_materials: '',
      air_quality: '',
      temperature_control: '',
      lighting: ''
    },
    general_observations: '',
    inspector_notes: '',
    inspection_date: new Date().toISOString().split('T')[0]
  });

  const queryClient = useQueryClient();

  // Initialize form data from inspection
  useEffect(() => {
    if (inspection && inspection.form_data) {
      setFormData(prev => ({
        ...prev,
        ...inspection.form_data
      }));
    }
  }, [inspection]);

  // Save form data mutation
  const saveFormMutation = useMutation({
    mutationFn: async (data) => {
      const formDataToSend = new FormData();
      formDataToSend.append('form_data', JSON.stringify(data));

      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/${inspection.id}/form-data`, {
        method: 'PUT',
        body: formDataToSend,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save form data');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Form saved successfully');
      queryClient.invalidateQueries(['monthly-inspections']);
      if (onSave) onSave();
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleGeneralInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    saveFormMutation.mutate(formData);
  };

  const getFieldLabel = (field) => {
    const labels = {
      sprinkler_system: 'Sprinkler System',
      fire_alarms: 'Fire Alarms',
      fire_extinguishers: 'Fire Extinguishers',
      emergency_exits: 'Emergency Exits',
      fire_doors: 'Fire Doors',
      smoking_areas: 'Smoking Areas',
      electrical_systems: 'Electrical Systems',
      kitchen_equipment: 'Kitchen Equipment',
      storage_areas: 'Storage Areas',
      maintenance_areas: 'Maintenance Areas',
      water_supply: 'Water Supply',
      waste_management: 'Waste Management',
      ventilation: 'Ventilation',
      pest_control: 'Pest Control',
      food_service: 'Food Service',
      sanitation: 'Sanitation',
      hazardous_materials: 'Hazardous Materials',
      air_quality: 'Air Quality',
      temperature_control: 'Temperature Control',
      lighting: 'Lighting'
    };
    return labels[field] || field;
  };

  const renderFormSection = (sectionTitle, sectionKey, fields) => (
    <div key={sectionKey} className="mb-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
        {sectionTitle}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.keys(fields).map((field) => (
          <div key={field} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              {getFieldLabel(field)}
            </label>
            <select
              value={formData[sectionKey][field] || ''}
              onChange={(e) => handleInputChange(sectionKey, field, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select status...</option>
              <option value="satisfactory">✅ Satisfactory</option>
              <option value="needs_attention">⚠️ Needs Attention</option>
              <option value="unsatisfactory">❌ Unsatisfactory</option>
              <option value="not_applicable">➖ Not Applicable</option>
            </select>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-blue-900">
              Monthly Inspection Form
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          <div className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Inspection Date
                </label>
                <input
                  type="date"
                  value={formData.inspection_date || ''}
                  onChange={(e) => handleGeneralInputChange('inspection_date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Month
                </label>
                <input
                  type="text"
                  value={`${new Date(0, inspection.month - 1).toLocaleString('default', { month: 'long' })} ${inspection.year}`}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <div className={`px-3 py-2 rounded-md text-sm font-medium ${
                  inspection.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                  inspection.status === 'inspector_signed' ? 'bg-yellow-100 text-yellow-800' :
                  inspection.status === 'deputy_signed' ? 'bg-green-100 text-green-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {inspection.status.replace('_', ' ')}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* Fire Safety Section */}
            {renderFormSection('Fire Safety', 'fire_safety', formData.fire_safety)}

            {/* Environmental Health Section */}
            {renderFormSection('Environmental Health', 'environmental_health', formData.environmental_health)}

            {/* General Observations */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                General Observations
              </label>
              <textarea
                value={formData.general_observations || ''}
                onChange={(e) => handleGeneralInputChange('general_observations', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter general observations about the facility..."
              />
            </div>

            {/* Inspector Notes */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Inspector Notes
              </label>
              <textarea
                value={formData.inspector_notes || ''}
                onChange={(e) => handleGeneralInputChange('inspector_notes', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter any additional notes or comments..."
              />
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saveFormMutation.isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saveFormMutation.isLoading ? 'Saving...' : 'Save Form'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InspectionForm;