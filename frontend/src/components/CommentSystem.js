import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CommentSystem = ({ recordId }) => {
  const [newComment, setNewComment] = useState('');
  const [commentType, setCommentType] = useState('general');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();

  // Fetch comments for the record
  const { data: comments, isLoading } = useQuery({
    queryKey: ['record-comments', recordId],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/records/${recordId}/comments`);
      if (!response.ok) throw new Error('Failed to fetch comments');
      return response.json();
    },
    enabled: !!recordId,
  });

  // Add comment mutation
  const addCommentMutation = useMutation({
    mutationFn: async (commentData) => {
      const formData = new FormData();
      formData.append('record_id', recordId);
      formData.append('comment', commentData.comment);
      formData.append('user', 'current_user'); // TODO: Get from auth context
      formData.append('comment_type', commentData.type);

      const response = await fetch(`${BACKEND_URL}/api/compliance/comments`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add comment');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Comment added successfully');
      queryClient.invalidateQueries(['record-comments', recordId]);
      setNewComment('');
      setCommentType('general');
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const handleSubmitComment = async () => {
    if (!newComment.trim()) {
      toast.error('Please enter a comment');
      return;
    }

    setIsSubmitting(true);
    await addCommentMutation.mutateAsync({
      comment: newComment,
      type: commentType,
    });
    setIsSubmitting(false);
  };

  const getCommentTypeIcon = (type) => {
    switch (type) {
      case 'issue':
        return '⚠️';
      case 'resolution':
        return '✅';
      case 'note':
        return '📝';
      default:
        return '💬';
    }
  };

  const getCommentTypeColor = (type) => {
    switch (type) {
      case 'issue':
        return 'bg-red-50 border-red-200';
      case 'resolution':
        return 'bg-green-50 border-green-200';
      case 'note':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString();
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-900"></div>
        <span className="ml-2 text-gray-600">Loading comments...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Add Comment Form */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Add Comment</h4>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comment Type
            </label>
            <select
              value={commentType}
              onChange={(e) => setCommentType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="general">General Comment</option>
              <option value="issue">Issue/Problem</option>
              <option value="resolution">Resolution/Fix</option>
              <option value="note">Important Note</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comment
            </label>
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Enter your comment here..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <button
            onClick={handleSubmitComment}
            disabled={isSubmitting || !newComment.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Adding...' : 'Add Comment'}
          </button>
        </div>
      </div>

      {/* Comments List */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">
          Comments ({comments?.length || 0})
        </h4>
        
        {comments && comments.length > 0 ? (
          <div className="space-y-3">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className={`border rounded-lg p-3 ${getCommentTypeColor(comment.type)}`}
              >
                <div className="flex items-start space-x-3">
                  <span className="text-lg">{getCommentTypeIcon(comment.type)}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{comment.user}</span>
                        <span className="px-2 py-1 text-xs bg-white rounded-full text-gray-600 capitalize">
                          {comment.type}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {formatTimestamp(comment.timestamp)}
                      </span>
                    </div>
                    <p className="text-gray-700 leading-relaxed">{comment.comment}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">💬</div>
            <p>No comments yet</p>
            <p className="text-sm">Be the first to add a comment!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentSystem;