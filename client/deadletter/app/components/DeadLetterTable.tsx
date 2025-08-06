// src/components/DeadLetterTable.tsx
import React, { useEffect, useState } from 'react';

interface DeadLetter {
  _id: string;
  message: string;
  topicName: string;
  subscriberName: string;
  endpoint: string;
  status: 'unacked' | 'retrying' | 'success' | 'failed';
  createdAt: string;
}

export const DeadLetterTable = () => {
  const [deadLetters, setDeadLetters] = useState<DeadLetter[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulated fetch - replace with actual API call
    const fetchData = async () => {
      setLoading(true);
      const response = await fetch('/api/deadletters');
      const data = await response.json();
      setDeadLetters(data);
      setLoading(false);
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading dead letters...</div>;

  return (
    <div className="overflow-x-auto mt-6">
      <table className="min-w-full bg-white shadow rounded">
        <thead>
          <tr className="bg-gray-200 text-left text-sm font-medium">
            <th className="p-3">Topic</th>
            <th className="p-3">Subscriber</th>
            <th className="p-3">Endpoint</th>
            <th className="p-3">Message</th>
            <th className="p-3">Status</th>
            <th className="p-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {deadLetters.map((item) => (
            <tr key={item._id} className="border-t hover:bg-gray-50 text-sm">
              <td className="p-3 font-mono text-xs">{item.topicName}</td>
              <td className="p-3">{item.subscriberName}</td>
              <td className="p-3 text-blue-600 truncate max-w-xs">{item.endpoint}</td>
              <td className="p-3 truncate max-w-xs">{item.message}</td>
              <td className="p-3">
                <span className={`px-2 py-1 rounded text-white text-xs ${
                  item.status === 'unacked' ? 'bg-red-500' :
                  item.status === 'retrying' ? 'bg-yellow-500' :
                  item.status === 'success' ? 'bg-green-500' :
                  'bg-gray-500'
                }`}>
                  {item.status}
                </span>
              </td>
              <td className="p-3">
                <button className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">
                  Retry
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
