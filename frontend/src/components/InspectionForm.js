import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const InspectionForm = ({ inspection, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    fire_safety: {
      // Fire Safety Section - Verbatim from Massachusetts DOC Form
      fire_alarm_system_tested: '',
      sprinkler_system_operational: '',
      fire_extinguishers_charged_accessible: '',
      emergency_exits_unlocked_unobstructed: '',
      exit_signs_illuminated: '',
      emergency_lighting_functional: '',
      fire_doors_properly_closed: '',
      smoke_dampers_operational: '',
      fire_pump_operational: '',
      standpipe_system_operational: '',
      fire_department_connection_accessible: '',
      hot_work_permits_current: '',
      flammable_liquids_properly_stored: '',
      electrical_panels_accessible: '',
      extension_cords_inspected: '',
      kitchen_hood_suppression_system: '',
      smoking_policy_enforced: '',
      fire_safety_training_current: '',
      fire_drill_conducted_monthly: '',
      fire_safety_equipment_inspected: ''
    },
    environmental_health: {
      // Environmental Health Section - Verbatim from Massachusetts DOC Form  
      potable_water_supply_adequate: '',
      water_temperature_appropriate: '',
      sewage_system_functioning: '',
      solid_waste_properly_disposed: '',
      hazardous_waste_properly_stored: '',
      pest_control_program_effective: '',
      food_service_areas_sanitary: '',
      food_storage_temperature_controlled: '',
      dishwashing_facilities_adequate: '',
      ventilation_systems_operational: '',
      air_quality_acceptable: '',
      temperature_control_adequate: '',
      lighting_levels_adequate: '',
      noise_levels_acceptable: '',
      laundry_facilities_sanitary: '',
      medical_waste_properly_handled: '',
      chemical_storage_compliant: '',
      plumbing_fixtures_operational: '',
      shower_facilities_adequate: '',
      toilet_facilities_adequate: ''
    },
    general_observations: '',
    inspector_notes: '',
    inspection_date: new Date().toISOString().split('T')[0],
    inspector_name: '',
    inspector_title: '',
    facility_representative: '',
    weather_conditions: '',
    inspection_time_start: '',
    inspection_time_end: ''
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
      // Fire Safety Labels - Verbatim from Massachusetts DOC Form
      fire_alarm_system_tested: 'Fire Alarm System Tested',
      sprinkler_system_operational: 'Sprinkler System Operational',
      fire_extinguishers_charged_accessible: 'Fire Extinguishers Charged & Accessible',
      emergency_exits_unlocked_unobstructed: 'Emergency Exits Unlocked & Unobstructed',
      exit_signs_illuminated: 'Exit Signs Illuminated',
      emergency_lighting_functional: 'Emergency Lighting Functional',
      fire_doors_properly_closed: 'Fire Doors Properly Closed',
      smoke_dampers_operational: 'Smoke Dampers Operational',
      fire_pump_operational: 'Fire Pump Operational',
      standpipe_system_operational: 'Standpipe System Operational',
      fire_department_connection_accessible: 'Fire Department Connection Accessible',
      hot_work_permits_current: 'Hot Work Permits Current',
      flammable_liquids_properly_stored: 'Flammable Liquids Properly Stored',
      electrical_panels_accessible: 'Electrical Panels Accessible',
      extension_cords_inspected: 'Extension Cords Inspected',
      kitchen_hood_suppression_system: 'Kitchen Hood Suppression System',
      smoking_policy_enforced: 'Smoking Policy Enforced',
      fire_safety_training_current: 'Fire Safety Training Current',
      fire_drill_conducted_monthly: 'Fire Drill Conducted Monthly',
      fire_safety_equipment_inspected: 'Fire Safety Equipment Inspected',
      
      // Environmental Health Labels - Verbatim from Massachusetts DOC Form
      potable_water_supply_adequate: 'Potable Water Supply Adequate',
      water_temperature_appropriate: 'Water Temperature Appropriate',
      sewage_system_functioning: 'Sewage System Functioning',
      solid_waste_properly_disposed: 'Solid Waste Properly Disposed',
      hazardous_waste_properly_stored: 'Hazardous Waste Properly Stored',
      pest_control_program_effective: 'Pest Control Program Effective',
      food_service_areas_sanitary: 'Food Service Areas Sanitary',
      food_storage_temperature_controlled: 'Food Storage Temperature Controlled',
      dishwashing_facilities_adequate: 'Dishwashing Facilities Adequate',
      ventilation_systems_operational: 'Ventilation Systems Operational',
      air_quality_acceptable: 'Air Quality Acceptable',
      temperature_control_adequate: 'Temperature Control Adequate',
      lighting_levels_adequate: 'Lighting Levels Adequate',
      noise_levels_acceptable: 'Noise Levels Acceptable',
      laundry_facilities_sanitary: 'Laundry Facilities Sanitary',
      medical_waste_properly_handled: 'Medical Waste Properly Handled',
      chemical_storage_compliant: 'Chemical Storage Compliant',
      plumbing_fixtures_operational: 'Plumbing Fixtures Operational',
      shower_facilities_adequate: 'Shower Facilities Adequate',
      toilet_facilities_adequate: 'Toilet Facilities Adequate'
    };
    return labels[field] || field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Touch-friendly button component
  const StatusButton = ({ value, currentValue, onChange, label, icon, color }) => {
    const isSelected = currentValue === value;
    return (
      <button
        type="button"
        onClick={() => onChange(value)}
        className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all duration-200 min-h-[80px] touch-manipulation ${
          isSelected
            ? `${color} border-current shadow-lg transform scale-105`
            : 'bg-white border-gray-300 hover:border-gray-400 hover:shadow-md'
        }`}
      >
        <div className="text-2xl mb-1">{icon}</div>
        <div className={`text-sm font-medium text-center ${isSelected ? 'text-white' : 'text-gray-700'}`}>
          {label}
        </div>
      </button>
    );
  };

  const StatusButtonGroup = ({ section, field, currentValue }) => {
    const statusOptions = [
      { value: 'satisfactory', label: 'Satisfactory', icon: '✅', color: 'bg-green-500 text-white' },
      { value: 'needs_attention', label: 'Needs Attention', icon: '⚠️', color: 'bg-yellow-500 text-white' },
      { value: 'unsatisfactory', label: 'Unsatisfactory', icon: '❌', color: 'bg-red-500 text-white' },
      { value: 'not_applicable', label: 'Not Applicable', icon: '➖', color: 'bg-gray-500 text-white' }
    ];

    return (
      <div className="grid grid-cols-2 gap-3">
        {statusOptions.map((option) => (
          <StatusButton
            key={option.value}
            value={option.value}
            currentValue={currentValue}
            onChange={(value) => handleInputChange(section, field, value)}
            label={option.label}
            icon={option.icon}
            color={option.color}
          />
        ))}
      </div>
    );
  };

  const renderFormSection = (sectionTitle, sectionKey, fields) => (
    <div key={sectionKey} className="mb-8">
      <h3 className="text-2xl font-semibold text-gray-900 mb-6 pb-3 border-b-2 border-gray-200 text-center">
        {sectionTitle}
      </h3>
      <div className="space-y-8">
        {Object.keys(fields).map((field) => (
          <div key={field} className="bg-gray-50 rounded-lg p-6 shadow-sm">
            <label className="block text-lg font-medium text-gray-800 mb-4 text-center">
              {getFieldLabel(field)}
            </label>
            <StatusButtonGroup
              section={sectionKey}
              field={field}
              currentValue={formData[sectionKey][field]}
            />
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[95vh] overflow-y-auto">
        <div className="p-6">
          {/* Header - iPad Optimized */}
          <div className="flex justify-between items-center mb-8 pb-4 border-b-2 border-blue-200">
            <div>
              <h2 className="text-3xl font-bold text-blue-900">
                Monthly Inspection Form
              </h2>
              <p className="text-lg text-gray-600 mt-1">
                {new Date(0, inspection.month - 1).toLocaleString('default', { month: 'long' })} {inspection.year}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-4xl p-2 rounded-full hover:bg-gray-100 touch-manipulation"
            >
              ×
            </button>
          </div>

          {/* Form Header Information */}
          <div className="mb-8 bg-blue-50 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Inspection Date
                </label>
                <input
                  type="date"
                  value={formData.inspection_date || ''}
                  onChange={(e) => handleGeneralInputChange('inspection_date', e.target.value)}
                  className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 touch-manipulation"
                />
              </div>
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  Status
                </label>
                <div className={`px-4 py-3 rounded-lg text-lg font-medium ${
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

          {/* Form Sections */}
          <div className="space-y-8">
            {/* Fire Safety Section */}
            {renderFormSection('🔥 Fire Safety', 'fire_safety', formData.fire_safety)}

            {/* Environmental Health Section */}
            {renderFormSection('🌱 Environmental Health', 'environmental_health', formData.environmental_health)}

            {/* General Observations - iPad Optimized */}
            <div className="mb-8 bg-gray-50 rounded-lg p-6 shadow-sm">
              <label className="block text-lg font-medium text-gray-800 mb-4">
                📝 General Observations
              </label>
              <textarea
                value={formData.general_observations || ''}
                onChange={(e) => handleGeneralInputChange('general_observations', e.target.value)}
                rows={6}
                className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 touch-manipulation"
                placeholder="Enter general observations about the facility..."
              />
            </div>

            {/* Inspector Notes - iPad Optimized */}
            <div className="mb-8 bg-gray-50 rounded-lg p-6 shadow-sm">
              <label className="block text-lg font-medium text-gray-800 mb-4">
                📋 Inspector Notes
              </label>
              <textarea
                value={formData.inspector_notes || ''}
                onChange={(e) => handleGeneralInputChange('inspector_notes', e.target.value)}
                rows={6}
                className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 touch-manipulation"
                placeholder="Enter any additional notes or comments..."
              />
            </div>
          </div>

          {/* Action Buttons - iPad Optimized */}
          <div className="flex flex-col sm:flex-row justify-end space-y-4 sm:space-y-0 sm:space-x-4 pt-8 border-t-2 border-gray-200">
            <button
              onClick={onClose}
              className="w-full sm:w-auto px-8 py-4 text-lg text-gray-600 border-2 border-gray-300 rounded-lg hover:bg-gray-50 touch-manipulation transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saveFormMutation.isLoading}
              className="w-full sm:w-auto px-8 py-4 text-lg bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 touch-manipulation transition-colors shadow-lg"
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