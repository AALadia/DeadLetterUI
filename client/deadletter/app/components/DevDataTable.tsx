"use client";
import React, { useEffect, useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import serverRequests from "../_lib/serverRequests";
import { DevData } from "../schemas/DevDataSchema";

export const DevDataTable: React.FC = () => {
  const { user, showSnackbar, localEndpointBaseUrl } = useAppContext();
  const [devData, setDevData] = useState<DevData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);

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
              <td className="max-w-xs text-xs truncate" title={JSON.stringify(item.data)}>{JSON.stringify(item.data)}</td>
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
    </div>
  );
};

export default DevDataTable;
