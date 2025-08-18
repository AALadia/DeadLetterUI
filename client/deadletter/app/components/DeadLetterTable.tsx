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
  const { user, showSnackbar,localEndpointUrl } = useAppContext();
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
    const data: DeadLetter[] = res.data || [];
    // Sort oldest -> latest based on createdAt (assumes ISO string)
    data.sort((a,b) => {
      const ta = a.createdAt ? Date.parse(a.createdAt) : 0;
      const tb = b.createdAt ? Date.parse(b.createdAt) : 0;
      return ta - tb; // ascending
    });
    setDeadLetters(data);
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
    const res = await serverRequests.replayDeadLetter(id, target, localEndpointUrl, user?._id || '');
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
    <div className="overflow-x-auto mt-6 w-full surface-card p-4">
      <table className="table-modern">
        <thead>
          <tr>
            <th>Topic</th>
            <th>Created At</th>
            <th>Message</th>
            <th>Error Message</th>
            <th>Status</th>
            <th>Retries</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {deadLetters.map((item) => {
            const statusClass = item.status === 'success' ? 'badge-success' : item.status === 'pending' ? 'badge-pending' : 'badge-failed';
            return (
              <tr key={item._id}>
                <td className="mono text-xs max-w-[160px] truncate" title={item.originalTopicPath || ''}>{item.originalTopicPath || '-'}</td>
                <td className="whitespace-nowrap text-xs opacity-80">{item.createdAt ? new Date(item.createdAt).toLocaleString() : '-'}</td>
                <td className="max-w-xs">
                  <a
                    onClick={() => { setOpenObjectViewer(true); setSelectedMessage(item.originalMessage); }}
                    className="text-[var(--accent)] truncate block overflow-hidden whitespace-nowrap hover:underline cursor-pointer"
                    title={JSON.stringify(item.originalMessage)}
                  >
                    {JSON.stringify(item.originalMessage)}
                  </a>
                </td>
                <td className="max-w-xs text-xs">
                  <span className="text-[var(--danger)]" title={item.errorMessage || ''}>{item.errorMessage}</span>
                </td>
                <td>
                  <span className={`badge ${statusClass}`}>{item.status}</span>
                </td>
                <td className="text-center text-xs">{item.retryCount}</td>
                <td>
                  <div className="flex gap-2 flex-wrap">
                    <button
                      className="btn btn-primary"
                      onClick={() => handleRetry(item._id, 'prod')}
                      disabled={item.status === 'success'}
                      title="Retry against production endpoint"
                    >Prod</button>
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleRetry(item._id, 'local')}
                      disabled={item.status === 'success'}
                      title="Retry against localhost (debug)"
                    >Local</button>
                  </div>
                </td>
              </tr>
            );
          })}
          {deadLetters.length === 0 && (
            <tr>
              <td colSpan={8} className="p-6 text-center text-sm opacity-60">No dead letters found.</td>
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
