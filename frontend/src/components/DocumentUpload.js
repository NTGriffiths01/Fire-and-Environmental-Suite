import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DocumentUpload = ({ recordId, onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadDescription, setUploadDescription] = useState('');
  const queryClient = useQueryClient();

  // Fetch existing documents for the record
  const { data: documents, isLoading } = useQuery({
    queryKey: ['record-documents', recordId],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/records/${recordId}/documents`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      return response.json();
    },
    enabled: !!recordId,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (formData) => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/records/${recordId}/documents`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Document uploaded successfully');
        queryClient.invalidateQueries(['record-documents', recordId]);
        setSelectedFiles([]);
        setUploadDescription('');
        if (onUploadSuccess) onUploadSuccess();
      } else {
        toast.error(data.errors.join(', '));
      }
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (documentId) => {
      const formData = new FormData();
      formData.append('deleted_by', 'current_user'); // TODO: Get from auth context
      
      const response = await fetch(`${BACKEND_URL}/api/compliance/documents/${documentId}`, {
        method: 'DELETE',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to delete document');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Document deleted successfully');
      queryClient.invalidateQueries(['record-documents', recordId]);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select at least one file');
      return;
    }

    setIsUploading(true);
    
    // Upload files one by one
    for (const file of selectedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('uploaded_by', 'current_user'); // TODO: Get from auth context
      if (uploadDescription) {
        formData.append('description', uploadDescription);
      }

      await uploadMutation.mutateAsync(formData);
    }

    setIsUploading(false);
  };

  const handleDownload = async (documentId, filename) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/compliance/documents/${documentId}/download`);
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download document');
    }
  };

  const handleDelete = (documentId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(documentId);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('image')) return '🖼️';
    if (fileType.includes('word')) return '📝';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
    return '📎';
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-900"></div>
        <span className="ml-2 text-gray-600">Loading documents...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Upload Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Upload Documents</h4>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Files
            </label>
            <input
              type="file"
              multiple
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.txt,.csv,.zip"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <input
              type="text"
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              placeholder="Brief description of the document(s)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleUpload}
              disabled={isUploading || selectedFiles.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? 'Uploading...' : `Upload ${selectedFiles.length} file(s)`}
            </button>
            
            {selectedFiles.length > 0 && (
              <span className="text-sm text-gray-600">
                {selectedFiles.map(f => f.name).join(', ')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">
          Uploaded Documents ({documents?.length || 0})
        </h4>
        
        {documents && documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div key={doc.id} className="bg-white border border-gray-200 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getFileIcon(doc.file_type)}</span>
                  <div>
                    <div className="font-medium text-gray-900">{doc.filename}</div>
                    <div className="text-sm text-gray-500">
                      {formatFileSize(doc.file_size)} • Uploaded by {doc.uploaded_by} • {new Date(doc.uploaded_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleDownload(doc.id, doc.filename)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                  >
                    Download
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📎</div>
            <p>No documents uploaded yet</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;