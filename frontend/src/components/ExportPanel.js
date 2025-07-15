import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ExportPanel = ({ facilityId, facilityName }) => {
  const [exportFormat, setExportFormat] = useState('json');
  const [isVisible, setIsVisible] = useState(false);

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async ({ format, facility_id }) => {
      const formData = new FormData();
      formData.append('format', format);
      if (facility_id) {
        formData.append('facility_id', facility_id);
      }

      const response = await fetch(`${BACKEND_URL}/api/compliance/export`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Export failed');
      return response.json();
    },
    onSuccess: (data) => {
      if (exportFormat === 'json') {
        // Download JSON data
        const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-export-${facilityId ? facilityName : 'all'}-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else if (exportFormat === 'csv') {
        // Download CSV data
        const blob = new Blob([data.content], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-export-${facilityId ? facilityName : 'all'}-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
      
      toast.success(`Exported ${data.total_records} records successfully`);
      setIsVisible(false);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const handleExport = () => {
    exportMutation.mutate({
      format: exportFormat,
      facility_id: facilityId,
    });
  };

  return (
    <div className="relative">
      {/* Export Button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2"
      >
        <span>📊</span>
        <span>Export Data</span>
      </button>

      {/* Export Panel */}
      {isVisible && (
        <div className="absolute right-0 top-12 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Export Compliance Data</h3>
              <button
                onClick={() => setIsVisible(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Export Scope */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Scope
                </label>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-900">
                    {facilityId ? `${facilityName} only` : 'All facilities'}
                  </div>
                  <div className="text-xs text-gray-500">
                    {facilityId ? 'Current facility data' : 'System-wide compliance data'}
                  </div>
                </div>
              </div>

              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={(e) => setExportFormat(e.target.value)}
                      className="text-green-600"
                    />
                    <span className="text-sm">JSON (Structured data)</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      value="csv"
                      checked={exportFormat === 'csv'}
                      onChange={(e) => setExportFormat(e.target.value)}
                      className="text-green-600"
                    />
                    <span className="text-sm">CSV (Spreadsheet compatible)</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      value="excel"
                      checked={exportFormat === 'excel'}
                      onChange={(e) => setExportFormat(e.target.value)}
                      className="text-green-600"
                    />
                    <span className="text-sm">Excel (Advanced spreadsheet)</span>
                  </label>
                </div>
              </div>

              {/* Export Info */}
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-sm text-blue-900">
                  <strong>Export includes:</strong>
                </div>
                <ul className="text-xs text-blue-800 mt-1 space-y-1">
                  <li>• Facility and function information</li>
                  <li>• Compliance schedules and frequencies</li>
                  <li>• Record status and due dates</li>
                  <li>• Task assignments and notes</li>
                  <li>• Document attachment indicators</li>
                </ul>
              </div>

              {/* Export Button */}
              <button
                onClick={handleExport}
                disabled={exportMutation.isLoading}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {exportMutation.isLoading ? 'Exporting...' : `Export as ${exportFormat.toUpperCase()}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExportPanel;