'use client';
// src/components/DeadLetterTable.tsx
import React, { useEffect, useState } from 'react';
import serverRequests from '../_lib/serverRequests';
import { useAppContext } from '../contexts/AppContext';
import { ObjectViewerModal } from "./ObjectViewerModal";
import { DeadLetter, Originaltopicpath } from '../schemas/DeadLetterSchema';
import { parseServiceAndEndpoint } from '../_utils/parseServiceAndEndpoint';



export const DeadLetterTable = () => {
  const [deadLetters, setDeadLetters] = useState<DeadLetter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, showSnackbar, localEndpointBaseUrl } = useAppContext();
  const [openObjectViewer, setOpenObjectViewer] = useState<boolean>(false);
  const [selectedMessage, setSelectedMessage] = useState<any>(null);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);
  const [manualEndpointModal, setManualEndpointModal] = useState<{ open: boolean; deadLetterId: string | null }>({ open: false, deadLetterId: null });
  const [errorMessageModal, setErrorMessageModal] = useState<DeadLetter | null>(null);
  const [manualEndpointValue, setManualEndpointValue] = useState<string>('');

  // Load saved manual endpoint from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('manualLocalEndpoint');
      if (saved) setManualEndpointValue(saved);
    }
  }, []);

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
    data.sort((a, b) => {
      const ta = a.createdAt ? Date.parse(a.createdAt) : 0;
      const tb = b.createdAt ? Date.parse(b.createdAt) : 0;
      return ta - tb; // ascending
    });
    console.log(data)
    setDeadLetters(data);
    setLoading(false);
  };

  useEffect(() => {
    if (user) {
      loadDeadLetters();
    }
  }, [user]);


  const handleRetry = async (id: string, target: 'prod' | 'local', localEndpointBaseUrl: string | null) => {
    const dl = deadLetters.find(d => d._id === id);
    if (!dl) return;

    setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, status: 'pending' } : d));
    const res = await serverRequests.replayDeadLetter(id, target, localEndpointBaseUrl, user?._id || '');
    showSnackbar(res, 4000)
    if (res.status === 200) {
      const updated = res.data;
      setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, ...updated } : d));
    } else {
      setDeadLetters(prev => prev.map(d => d._id === id ? { ...d, status: 'failed' } : d));
    }
  };

  const toggleMockMenu = (rowId: string) => {
    setOpenDropdownId(prev => (prev === rowId ? null : rowId));

  };

  const handleEndpointSelect = (id: string, option: string) => {

    if (localEndpointBaseUrl === null) {
      showSnackbar({ status: 400, message: 'Please set a valid Local Endpoint URL in the menu above before retrying locally.' });
      return
    }

  setOpenDropdownId(null);
    console.log('Selected mock option', option, 'for id', id);

    const localApiEndpoint = `${localEndpointBaseUrl}${option}`;
    console.log('Local API endpoint:', localApiEndpoint);
    void handleRetry(id, 'local', localApiEndpoint);
  };

  const handleManualEndpointOpen = (id: string) => {
    setOpenDropdownId(null);
    // Load saved value from localStorage when opening modal
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('manualLocalEndpoint');
      setManualEndpointValue(saved || '');
    }
    setManualEndpointModal({ open: true, deadLetterId: id });
  };

  const handleManualEndpointSubmit = () => {
    if (!manualEndpointModal.deadLetterId || !manualEndpointValue.trim()) {
      showSnackbar({ status: 400, message: 'Please enter a valid endpoint.' });
      return;
    }
    const endpoint = manualEndpointValue.trim();
    // Save to localStorage for next time
    if (typeof window !== 'undefined') {
      localStorage.setItem('manualLocalEndpoint', endpoint);
    }
    // If the endpoint starts with http, use it as-is; otherwise prepend the base URL
    let localApiEndpoint: string;
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      localApiEndpoint = endpoint;
    } else {
      if (localEndpointBaseUrl === null) {
        showSnackbar({ status: 400, message: 'Please set a valid Local Endpoint URL in the menu above, or enter a full URL.' });
        return;
      }
      localApiEndpoint = `${localEndpointBaseUrl}${endpoint.startsWith('/') ? endpoint.slice(1) : endpoint}`;
    }
    console.log('Manual local API endpoint:', localApiEndpoint);
    void handleRetry(manualEndpointModal.deadLetterId, 'local', localApiEndpoint);
    setManualEndpointModal({ open: false, deadLetterId: null });
  };

  if (!user) return <div className="mt-6 text-sm">Please log in to view dead letters.</div>;
  if (loading) return <div>Loading dead letters...</div>;
  if (error) return <div className="text-red-600 text-sm">{error}</div>;

  function getTopicNameFromPath(topicPath:Originaltopicpath|undefined):string|undefined {
  if (!topicPath) return undefined;
  const parts = topicPath.split('/');
  return parts[parts.length - 1];
  }

  return (
    <div className="overflow-y mt-6 w-full surface-card p-4 h-3/4">
      <table className="table-modern">
        <thead>
          <tr>
            <th>ID</th>
            <th>Topic</th>
            <th>Created At</th>
            <th>Message</th>
            <th>Project Errors</th>
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
                <td className="mono text-xs" title={item._id}>{item._id}</td>
                <td className="mono text-xs max-w-[160px] truncate" title={getTopicNameFromPath(item.originalTopicPath) || ''}>{getTopicNameFromPath(item.originalTopicPath) || '-'}</td>
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
                  {item.serviceErrorMessage && item.serviceErrorMessage.length > 0 ? (
                    <span
                      className="text-[var(--danger)] cursor-pointer hover:underline"
                      onClick={() => setErrorMessageModal(item)}
                    >
                      {item.serviceErrorMessage.length} {item.serviceErrorMessage.length === 1 ? 'error' : 'errors'}
                    </span>
                  ) : null}
                </td>
                <td>
                  <span className={`badge ${statusClass}`}>{item.status}</span>
                </td>
                <td className="text-center text-xs">{item.retryCount}</td>
                <td>
                  <div className="flex gap-2 flex-wrap">
                    <button
                      className="btn btn-primary"
                      onClick={() => handleRetry(item._id, 'prod',null)}
                      disabled={item.status === 'success'}
                      title="Retry against production endpoint"
                    >Prod</button>
                    <div className="relative inline-block">
                      <button
                        className="btn btn-secondary"
                        onClick={() => toggleMockMenu(item._id)}
                        disabled={item.status === 'success'}
                        title="Retry against localhost (choose endpoint)"
                        aria-haspopup="menu"
                        aria-expanded={openDropdownId === item._id}
                      >
                        Local ▾
                      </button>
                      {openDropdownId === item._id ? (
                        <div
                          role="menu"
                          className="absolute z-50 mt-1 min-w-[160px] max-h-60 overflow-auto rounded-md right-0 top-full"
                          style={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border-color)',
                            boxShadow: 'var(--shadow-sm)',
                            maxWidth: 'min(320px, 90vw)'
                          }}
                        >
                          {(((item.endPoints ?? []) as Array<string>)).map(opt => {
                            const { service, endpoint } = parseServiceAndEndpoint(opt);
                            if (!service || !endpoint) return null;
                            return (
                              <button
                                key={opt}
                                role="menuitem"
                                className="w-full text-left px-3 py-2 text-sm hover:bg-[rgba(0,0,0,0.04)]"
                                onClick={() => handleEndpointSelect(item._id, endpoint)}
                              >
                                {service}/{endpoint}
                              </button>
                            );
                          })}
                          <hr className="my-1 border-t" style={{ borderColor: 'var(--border-color)' }} />
                          <button
                            role="menuitem"
                            className="w-full text-left px-3 py-2 text-sm hover:bg-[rgba(0,0,0,0.04)] italic"
                            style={{ color: 'var(--accent)' }}
                            onClick={() => handleManualEndpointOpen(item._id)}
                          >
                            Manually Enter Local Endpoint
                          </button>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </td>
              </tr>
            );
          })}
          {deadLetters.length === 0 && (
            <tr>
              <td colSpan={9} className="p-6 text-center text-sm opacity-60">No dead letters found.</td>
            </tr>
          )}
        </tbody>
      </table>
      <ObjectViewerModal
        open={openObjectViewer}
        onClose={() => setOpenObjectViewer(false)}
        data={selectedMessage}
      />
      {/* Manual Endpoint Entry Modal */}
      {manualEndpointModal.open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={() => setManualEndpointModal({ open: false, deadLetterId: null })}
        >
          <div
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md"
            style={{ background: 'var(--surface)', border: '1px solid var(--border-color)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold mb-4">Enter Local Endpoint</h3>
            <p className="text-sm mb-3 opacity-70">
              Enter an endpoint path (e.g., <code>api/test</code>) or a full URL (e.g., <code>http://localhost:3000/api/test</code>).
            </p>
            <input
              type="text"
              value={manualEndpointValue}
              onChange={(e) => setManualEndpointValue(e.target.value)}
              placeholder="api/endpoint or http://localhost:3000/api/endpoint"
              className="w-full px-3 py-2 rounded border text-sm mb-4"
              style={{ borderColor: 'var(--border-color)', background: 'var(--surface-alt, #fff)' }}
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') handleManualEndpointSubmit(); }}
            />
            <div className="flex justify-end gap-2">
              <button
                className="btn btn-secondary"
                onClick={() => setManualEndpointModal({ open: false, deadLetterId: null })}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleManualEndpointSubmit}
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Project Errors Modal */}
      {errorMessageModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={() => setErrorMessageModal(null)}
        >
          <div
            className="rounded-lg shadow-lg p-6 w-[90vw] h-[90vh] flex flex-col"
            style={{ background: 'var(--surface)', border: '1px solid var(--border-color)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 shrink-0">
              <h3 className="text-lg font-semibold">Project Errors</h3>
            </div>
            <div className="overflow-auto flex-1 flex flex-col gap-3">
              {errorMessageModal.serviceErrorMessage?.map((err, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-xs font-semibold" style={{ color: 'var(--accent)' }}>
                      {err.serviceEndpoint || 'Unknown endpoint'}
                    </div>
                    <button
                      className="text-xs text-[var(--accent)] hover:underline"
                      onClick={async () => {
                        const text = [
                          `Endpoint: ${err.serviceEndpoint || 'Unknown'}`,
                          `Topic: ${errorMessageModal.originalTopicPath || 'Unknown'}`,
                          '',
                          'Original Message:',
                          JSON.stringify(errorMessageModal.originalMessage, null, 2),
                          '',
                          'Traceback:',
                          err.traceback || 'No traceback',
                        ].join('\n');
                        await navigator.clipboard.writeText(text);
                        showSnackbar({ status: 200, message: 'Copied error context to clipboard' });
                      }}
                    >
                      Copy Context
                    </button>
                  </div>
                  <pre
                    className="text-sm mono whitespace-pre-wrap break-words p-3 rounded"
                    style={{ background: 'var(--surface-alt)', border: '1px solid var(--border-color)', color: 'var(--danger)' }}
                  >
                    {err.traceback || 'No traceback'}
                  </pre>
                </div>
              ))}
            </div>
            <div className="flex justify-end mt-4 shrink-0">
              <button className="btn btn-primary" onClick={() => setErrorMessageModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
