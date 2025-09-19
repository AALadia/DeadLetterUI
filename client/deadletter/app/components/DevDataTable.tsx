"use client";
import React, { useEffect, useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import serverRequests from "../_lib/serverRequests";
import { DevData } from "../schemas/DevDataSchema";
import { ObjectViewerModal } from "./ObjectViewerModal";

export const DevDataTable: React.FC = () => {
  const { user, showSnackbar, localEndpointBaseUrl } = useAppContext();
  const [devData, setDevData] = useState<DevData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [openObjectViewer, setOpenObjectViewer] = useState<boolean>(false);
  const [selectedJson, setSelectedJson] = useState<any>(null);
  const [deletingAll, setDeletingAll] = useState<boolean>(false);

  const loadDevData = async () => {
    setLoading(true);
    setError(null);
    if (!user) return;
    const res = await serverRequests.getDevDataMessages(user._id);
    console.log(res);
    if (res.status !== 200) {
      setError(res.message || "Failed to load dev data");
      setLoading(false);
      return;
    }
    setDevData(res.data || []);
    setLoading(false);
  };

  useEffect(() => {
    if (user) loadDevData();
  }, [user]);
  const handleDeleteAll = async () => {
    if (!user?._id) return;
    const confirmed = typeof window !== 'undefined' ? window.confirm('Delete ALL dev data messages? This cannot be undone.') : true;
    if (!confirmed) return;
    setDeletingAll(true);
    const res = await serverRequests.deleteAllDevDataMessages(user._id);
    showSnackbar(res, 4000);
    setDeletingAll(false);
    if (res.status === 200) {
      await loadDevData();
    }
  };

  const handleRetry = async (id: string,projectName:string) => {
    if (!localEndpointBaseUrl) {
      showSnackbar({ status: 400, message: "Set a valid Local Endpoint URL above before retrying." });
      return;
    }
    setRetryingId(id);
    // For demo, just use the base URL as endpoint; adjust as needed
    const res = await serverRequests.replayDevDataMessage(id, localEndpointBaseUrl,projectName);
    showSnackbar(res, 4000);
    setRetryingId(null);
    if (res.status === 200) loadDevData();
  };

  if (loading) return <div>Loading dev data...</div>;
  if (error) return <div className="text-red-600 text-sm">{error}</div>;

  return (
    <div className="overflow-x-auto mt-6 w-full surface-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold" style={{ color: 'var(--color-text-strong,#1f2937)' }}>Dev Data Messages</h2>
        <div className="flex gap-2">
          <button
            className="btn btn-ghost"
            style={{ color: 'var(--danger,#dc2626)', border: '1px solid var(--danger,#dc2626)' }}
            onClick={handleDeleteAll}
            disabled={deletingAll || devData.length === 0}
            title="Delete all dev data messages"
          >
            {deletingAll ? 'Deleting…' : 'Delete All'}
          </button>
        </div>
      </div>
      <table className="table-modern">
        <thead>
          <tr>
            <th>ID</th>
            <th>Created At</th>
            <th>From Project</th>
            <th>Data</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devData.map((item) => (
            <tr key={item._id}>
              <td className="mono text-xs max-w-[160px] truncate" title={item._id}>{item._id}</td>
              <td className="whitespace-nowrap text-xs opacity-80">{item.createdAt ? new Date(item.createdAt).toLocaleString() : "-"}</td>
              <td className="text-xs">{item.fromProject}</td>
              <td className="max-w-xs">
                <a
                  onClick={() => { setOpenObjectViewer(true); setSelectedJson(item.data); }}
                  className="text-[var(--accent)] truncate block overflow-hidden whitespace-nowrap hover:underline cursor-pointer text-xs"
                  title={JSON.stringify(item.data)}
                >
                  {JSON.stringify(item.data)}
                </a>
              </td>
              <td>
                <button
                  className="btn btn-secondary"
                  onClick={() => handleRetry(item._id,item.fromProject)}
                  disabled={retryingId === item._id}
                  title="Retry this dev data message"
                >
                  {retryingId === item._id ? "Retrying..." : "Retry"}
                </button>
              </td>
            </tr>
          ))}
          {devData.length === 0 && (
            <tr>
              <td colSpan={5} className="p-6 text-center text-sm opacity-60">No dev data found.</td>
            </tr>
          )}
        </tbody>
      </table>
      <ObjectViewerModal
        open={openObjectViewer}
        onClose={() => setOpenObjectViewer(false)}
        data={selectedJson}
      />
    </div>
  );
};

export default DevDataTable;
