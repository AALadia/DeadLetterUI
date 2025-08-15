'use client';
// src/components/DeadLetterTable.tsx
import React, { useEffect, useState } from 'react';
import serverRequests from '../_lib/serverRequests';
import { useAppContext } from '../contexts/AppContext';
import { ObjectViewerModal } from "./ObjectViewerModal";
import { DeadLetter } from '../schemas/DeadLetterSchema';



export const DeadLetterTable = () => {
  const [deadLetters, setDeadLetters] = useState<DeadLetter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, showSnackbar } = useAppContext();
  const [openObjectViewer, setOpenObjectViewer] = useState<boolean>(false);
  const [selectedMessage, setSelectedMessage] = useState<any>(null);

  const loadDeadLetters = async () => {
    setLoading(true);
    setError(null);
    const res = await serverRequests.listDeadLetters(null);
    console.log(res)
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


  const handleRetry = async (id: string, target: 'prod' | 'local') => {
    const dl = deadLetters.find(d => d._id === id);
    if (!dl) return;

    setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, status: 'pending' } : d));
    const res = await serverRequests.replayDeadLetter(id,target, user?._id || '');
    showSnackbar(res,4000)
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
            <th className="p-3">Subscription</th>
            <th className="p-3">Message</th>
            <th className="p-3">Error Message</th>
            <th className="p-3">Status</th>
            <th className="p-3">Retries</th>
            <th className="p-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {deadLetters.map((item) => (
            <tr key={item._id} className="border-t hover:bg-gray-50 text-sm">
              <td className="p-3 font-mono text-xs">{item.topic}</td>
              <td className="p-3">{item.subscription}</td>
              <td className="p-3 max-w-xs">
                <a
                  onClick={() => {
                    setOpenObjectViewer(true);
                    setSelectedMessage(item.originalMessage);
                  }}
                  className="text-blue-600 truncate block overflow-hidden whitespace-nowrap hover:underline"
                  title={JSON.stringify(item.originalMessage)} // tooltip with full text
                >
                  {JSON.stringify(item.originalMessage)}
                </a>
              </td>
              <td className="p-3 max-w-xs">
                <span className="text-red-600">{item.errorMessage}</span>
              </td>
              <td className="p-3">
                <span className={`px-2 py-1 rounded text-white text-xs ${item.status === 'pending' ? 'bg-yellow-500' :
                    item.status === 'success' ? 'bg-green-500' :
                      'bg-red-500'
                  }`}>
                  {item.status}
                </span>
              </td>
              <td className="p-3 text-center">{item.retryCount}</td>
              <td className="p-3">
                <div className="flex gap-1 flex-wrap">
                  <button
                    className="px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                    onClick={() => handleRetry(item._id, 'prod')}
                    disabled={item.status === 'success'}
                    title="Retry against production endpoint"
                  >
                    Retry Prod
                  </button>
                  <button
                    className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    onClick={() => handleRetry(item._id, 'local')}
                    disabled={item.status === 'success'}
                    title="Retry against localhost (debug)"
                  >
                    Retry Local
                  </button>
                </div>
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
      <ObjectViewerModal
        open={openObjectViewer}
        onClose={() => setOpenObjectViewer(false)}
        data={selectedMessage}
      />
    </div>
  );
};
