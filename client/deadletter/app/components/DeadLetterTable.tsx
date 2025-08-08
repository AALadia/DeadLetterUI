'use client';
// src/components/DeadLetterTable.tsx
import React, { useEffect, useState } from 'react';
import serverRequests from '../_lib/serverRequests';
import { useAppContext } from '../contexts/AppContext';

interface DeadLetterRow {
  _id: string;
  originalMessage: any;
  topicName: string;
  subscriberName: string;
  endpoint: string;
  status: 'pending' | 'success' | 'failed';
  retryCount: number;
  createdAt: string;
  lastTriedAt?: string | null;
}

export const DeadLetterTable = () => {
  const [deadLetters, setDeadLetters] = useState<DeadLetterRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAppContext();

  const loadDeadLetters = async () => {
    setLoading(true);
    setError(null);
    const res = await serverRequests.listDeadLetters();
    if (res.status !== 200) {
      const msg = res.message || 'Failed to load dead letters';
      setError(`${msg}${res.status === 401 ? ' (unauthorized - please re-login)' : ''}`);
      setLoading(false);
      return;
    }
    setDeadLetters(res.data || []);
    setLoading(false);
  };

  useEffect(() => {
    if (user) {
      loadDeadLetters();
    }
  }, [user]);

  const handleRetry = async (id: string) => {
    const dl = deadLetters.find(d => d._id === id);
    if (!dl) return;

    setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, status: 'pending' } : d));
    const res = await serverRequests.replayDeadLetter(id, user?._id || '');
    if (res.status === 200) {
      const updated = res.data;
      setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, ...updated } : d));
    } else {
      setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, status: 'failed' } : d));
    }
  };

  if (!user) return <div className="mt-6 text-sm">Please log in to view dead letters.</div>;
  if (loading) return <div>Loading dead letters...</div>;
  if (error) return <div className="text-red-600 text-sm">{error}</div>;

  return (
    <div className="overflow-x-auto mt-6 w-full">
      <table className="min-w-full bg-white shadow rounded">
        <thead>
          <tr className="bg-gray-200 text-left text-sm font-medium">
            <th className="p-3">Topic</th>
            <th className="p-3">Subscriber</th>
            <th className="p-3">Endpoint</th>
            <th className="p-3">Error</th>
            <th className="p-3">Status</th>
            <th className="p-3">Retries</th>
            <th className="p-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {deadLetters.map((item) => (
            <tr key={item._id} className="border-t hover:bg-gray-50 text-sm">
              <td className="p-3 font-mono text-xs">{item.topicName}</td>
              <td className="p-3">{item.subscriberName}</td>
              <td className="p-3 text-blue-600 truncate max-w-xs" title={item.endpoint}>{item.endpoint}</td>
              <td className="p-3 truncate max-w-xs" title={item.originalMessage?.errorMessage}>{item.originalMessage?.errorMessage || '-'}</td>
              <td className="p-3">
                <span className={`px-2 py-1 rounded text-white text-xs ${
                  item.status === 'pending' ? 'bg-yellow-500' :
                  item.status === 'success' ? 'bg-green-500' :
                  'bg-red-500'
                }`}>
                  {item.status}
                </span>
              </td>
              <td className="p-3 text-center">{item.retryCount}</td>
              <td className="p-3">
                <button
                  className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  onClick={() => handleRetry(item._id)}
                  disabled={item.status === 'success'}
                >
                  Retry
                </button>
              </td>
            </tr>
          ))}
          {deadLetters.length === 0 && (
            <tr>
              <td colSpan={7} className="p-4 text-center text-sm text-gray-500">No dead letters found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};
