import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DigitalSignature = ({ inspection, onClose }) => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [signatureType, setSignatureType] = useState('inspector');
  const [signerName, setSignerName] = useState('');
  const [hasSignature, setHasSignature] = useState(false);
  const queryClient = useQueryClient();

  // Get existing signatures
  const { data: signatures } = useQuery({
    queryKey: ['inspection-signatures', inspection.id],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/${inspection.id}/signatures`);
      if (!response.ok) throw new Error('Failed to fetch signatures');
      return response.json();
    },
  });

  // Add signature mutation
  const addSignatureMutation = useMutation({
    mutationFn: async (data) => {
      const formData = new FormData();
      formData.append('signature_type', data.signature_type);
      formData.append('signed_by', data.signed_by);
      formData.append('signature_data', data.signature_data);
      formData.append('ip_address', data.ip_address);
      formData.append('user_agent', navigator.userAgent);

      const response = await fetch(`${BACKEND_URL}/api/monthly-inspections/${inspection.id}/signature`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add signature');
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries(['inspection-signatures']);
      queryClient.invalidateQueries(['monthly-inspections']);
      clearCanvas();
      setSignerName('');
      setHasSignature(false);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, []);

  const startDrawing = (e) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    ctx.stroke();
    
    setHasSignature(true);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  };

  const saveSignature = async () => {
    if (!hasSignature) {
      toast.error('Please provide a signature');
      return;
    }

    if (!signerName.trim()) {
      toast.error('Please enter your name');
      return;
    }

    const canvas = canvasRef.current;
    const signatureData = canvas.toDataURL('image/png');

    // Get IP address (simplified)
    const ipAddress = await fetch('https://api.ipify.org?format=json')
      .then(res => res.json())
      .then(data => data.ip)
      .catch(() => 'unknown');

    addSignatureMutation.mutate({
      signature_type: signatureType,
      signed_by: signerName,
      signature_data: signatureData,
      ip_address: ipAddress,
    });
  };

  const getSignatureStatus = (type) => {
    const signature = signatures?.find(s => s.signature_type === type);
    return signature ? {
      exists: true,
      signed_by: signature.signed_by,
      signed_at: signature.signed_at,
      verification_hash: signature.verification_hash
    } : { exists: false };
  };

  const inspectorSignature = getSignatureStatus('inspector');
  const deputySignature = getSignatureStatus('deputy');

  const canSignAsInspector = !inspectorSignature.exists;
  const canSignAsDeputy = !deputySignature.exists && inspectorSignature.exists;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-blue-900">
              Digital Signatures
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Signature Status */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Signature Status</h3>
            <div className="space-y-3">
              <div className={`p-4 rounded-lg border ${
                inspectorSignature.exists ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Inspector Signature</div>
                    {inspectorSignature.exists ? (
                      <div className="text-sm text-green-600">
                        ✅ Signed by {inspectorSignature.signed_by} on {new Date(inspectorSignature.signed_at).toLocaleDateString()}
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">⏳ Pending signature</div>
                    )}
                  </div>
                  {inspectorSignature.exists && (
                    <div className="text-xs text-gray-400">
                      Hash: {inspectorSignature.verification_hash?.substring(0, 8)}...
                    </div>
                  )}
                </div>
              </div>

              <div className={`p-4 rounded-lg border ${
                deputySignature.exists ? 'bg-green-50 border-green-200' : 
                inspectorSignature.exists ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Deputy of Operations Signature</div>
                    {deputySignature.exists ? (
                      <div className="text-sm text-green-600">
                        ✅ Signed by {deputySignature.signed_by} on {new Date(deputySignature.signed_at).toLocaleDateString()}
                      </div>
                    ) : inspectorSignature.exists ? (
                      <div className="text-sm text-yellow-600">⏳ Awaiting deputy signature</div>
                    ) : (
                      <div className="text-sm text-gray-500">⏳ Waiting for inspector signature first</div>
                    )}
                  </div>
                  {deputySignature.exists && (
                    <div className="text-xs text-gray-400">
                      Hash: {deputySignature.verification_hash?.substring(0, 8)}...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Signature Canvas */}
          {(canSignAsInspector || canSignAsDeputy) && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Signature</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Signature Type
                  </label>
                  <select
                    value={signatureType}
                    onChange={(e) => setSignatureType(e.target.value)}
                    className="w-full md:w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {canSignAsInspector && (
                      <option value="inspector">Inspector (Fire Safety Officer / Environmental Health Safety Officer)</option>
                    )}
                    {canSignAsDeputy && (
                      <option value="deputy">Deputy of Operations</option>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={signerName}
                    onChange={(e) => setSignerName(e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full md:w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Digital Signature
                  </label>
                  <div className="border border-gray-300 rounded-md p-4 bg-gray-50">
                    <canvas
                      ref={canvasRef}
                      width={600}
                      height={200}
                      className="border border-gray-300 bg-white rounded cursor-crosshair"
                      onMouseDown={startDrawing}
                      onMouseMove={draw}
                      onMouseUp={stopDrawing}
                      onMouseLeave={stopDrawing}
                    />
                    <div className="mt-2 text-sm text-gray-500">
                      Click and drag to sign above
                    </div>
                  </div>
                </div>

                <div className="flex space-x-4">
                  <button
                    onClick={clearCanvas}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Clear
                  </button>
                  <button
                    onClick={saveSignature}
                    disabled={addSignatureMutation.isLoading || !hasSignature || !signerName.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {addSignatureMutation.isLoading ? 'Saving...' : 'Save Signature'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Workflow Information */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Signature Workflow</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="space-y-2 text-sm">
                <div className="flex items-center space-x-2">
                  <span className={inspectorSignature.exists ? 'text-green-600' : 'text-gray-400'}>
                    {inspectorSignature.exists ? '✅' : '1️⃣'}
                  </span>
                  <span>Inspector (FSO/EHSO) completes and signs the inspection</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={deputySignature.exists ? 'text-green-600' : inspectorSignature.exists ? 'text-yellow-600' : 'text-gray-400'}>
                    {deputySignature.exists ? '✅' : inspectorSignature.exists ? '⏳' : '2️⃣'}
                  </span>
                  <span>Email notification sent to Deputy of Operations</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={deputySignature.exists ? 'text-green-600' : 'text-gray-400'}>
                    {deputySignature.exists ? '✅' : '3️⃣'}
                  </span>
                  <span>Deputy of Operations reviews and signs</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={deputySignature.exists ? 'text-green-600' : 'text-gray-400'}>
                    {deputySignature.exists ? '✅' : '4️⃣'}
                  </span>
                  <span>Form automatically populates to Compliance Tracking Tool</span>
                </div>
              </div>
            </div>
          </div>

          {/* Close Button */}
          <div className="flex justify-end">
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

export default DigitalSignature;