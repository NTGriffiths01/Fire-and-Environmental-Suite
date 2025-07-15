import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TaskAssignment = ({ recordId, currentAssignee, onAssignmentChange }) => {
  const [isAssigning, setIsAssigning] = useState(false);
  const [selectedUser, setSelectedUser] = useState('');
  const [assignmentNotes, setAssignmentNotes] = useState('');
  const queryClient = useQueryClient();

  // Mock users - in real app, this would come from user management API
  const availableUsers = [
    { id: 'user1', name: 'John Smith', email: 'john@madoc.gov' },
    { id: 'user2', name: 'Jane Doe', email: 'jane@madoc.gov' },
    { id: 'user3', name: 'Mike Johnson', email: 'mike@madoc.gov' },
    { id: 'user4', name: 'Sarah Wilson', email: 'sarah@madoc.gov' },
  ];

  // Fetch current task assignments
  const { data: assignments } = useQuery({
    queryKey: ['task-assignments', recordId],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/tasks/assignments?record_id=${recordId}`);
      if (!response.ok) throw new Error('Failed to fetch assignments');
      return response.json();
    },
    enabled: !!recordId,
  });

  // Assignment mutation
  const assignMutation = useMutation({
    mutationFn: async (assignmentData) => {
      const formData = new FormData();
      formData.append('record_id', recordId);
      formData.append('assigned_to', assignmentData.assigned_to);
      formData.append('assigned_by', 'current_user'); // TODO: Get from auth context
      if (assignmentData.notes) {
        formData.append('notes', assignmentData.notes);
      }

      const response = await fetch(`${BACKEND_URL}/api/compliance/tasks/assign`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Assignment failed');
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast.success('Task assigned successfully');
      queryClient.invalidateQueries(['task-assignments']);
      setSelectedUser('');
      setAssignmentNotes('');
      if (onAssignmentChange) onAssignmentChange(data.assigned_to);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const handleAssign = async () => {
    if (!selectedUser) {
      toast.error('Please select a user to assign');
      return;
    }

    setIsAssigning(true);
    await assignMutation.mutateAsync({
      assigned_to: selectedUser,
      notes: assignmentNotes,
    });
    setIsAssigning(false);
  };

  const getUserName = (userId) => {
    const user = availableUsers.find(u => u.id === userId);
    return user ? user.name : userId;
  };

  return (
    <div className="space-y-4">
      {/* Current Assignment */}
      {currentAssignee && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-sm font-medium text-blue-900">
              Currently assigned to: {getUserName(currentAssignee)}
            </span>
          </div>
        </div>
      )}

      {/* Assignment Form */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">
          {currentAssignee ? 'Reassign Task' : 'Assign Task'}
        </h4>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assign to User
            </label>
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a user...</option>
              {availableUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name} ({user.email})
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assignment Notes (optional)
            </label>
            <textarea
              value={assignmentNotes}
              onChange={(e) => setAssignmentNotes(e.target.value)}
              placeholder="Add any specific instructions or notes for the assignee..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <button
            onClick={handleAssign}
            disabled={isAssigning || !selectedUser}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAssigning ? 'Assigning...' : 'Assign Task'}
          </button>
        </div>
      </div>

      {/* Assignment History */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">Assignment History</h4>
        
        <div className="space-y-2">
          {assignments && assignments.length > 0 ? (
            assignments.map((assignment, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900">
                      Assigned to {getUserName(assignment.assigned_to)}
                    </div>
                    <div className="text-sm text-gray-500">
                      Due: {new Date(assignment.due_date).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {assignment.frequency} task
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-4 text-gray-500">
              <div className="text-2xl mb-2">👥</div>
              <p>No assignment history</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskAssignment;