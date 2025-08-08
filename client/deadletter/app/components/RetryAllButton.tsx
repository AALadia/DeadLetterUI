// src/components/RetryAllButton.tsx
import React, { useState } from 'react';
import serverRequests from '../_lib/serverRequests';
import { useAppContext } from '../contexts/AppContext';

export const RetryAllButton = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { user } = useAppContext();

  const handleRetryAll = async () => {
    if (!user) {
      setMessage('Please login first');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const listRes = await serverRequests.listDeadLetters();
      if (listRes.status !== 200) {
        setMessage('Failed to load dead letters');
        setLoading(false);
        return;
      }
      const deadLetters = listRes.data || [];
      let success = 0;
      for (const dl of deadLetters) {
        if (dl.status === 'success') continue; // skip already succeeded
        const res = await serverRequests.replayDeadLetter(dl._id, user._id);
        if (res.status === 200 && res.data.status === 'success') success++;
      }
      setMessage(`Replay complete. Successful: ${success}/${deadLetters.length}`);
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
        disabled={loading || !user}
      >
        {loading ? 'Retrying...' : '🔁 Retry All'}
      </button>
      {message && <span className="text-sm text-gray-600">{message}</span>}
    </div>
  );
};