// src/components/RetryAllButton.tsx
import React, { useState } from 'react';

export const RetryAllButton = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleRetryAll = async () => {
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch('/api/deadletters/retry-all', {
        method: 'POST',
      });
      const result = await response.json();
      setMessage(result.message || 'Retry request sent.');
    } catch (err) {
      setMessage('Error while retrying messages.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center gap-4 mb-4">
      <button
        className="bg-blue-700 text-white px-4 py-2 text-sm rounded hover:bg-blue-800 disabled:opacity-50"
        onClick={handleRetryAll}
        disabled={loading}
      >
        {loading ? 'Retrying...' : '🔁 Retry All'}
      </button>
      {message && <span className="text-sm text-gray-600">{message}</span>}
    </div>
  );
};