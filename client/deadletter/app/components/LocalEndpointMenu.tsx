"use client";
import React, { useState } from 'react';

/*
  LocalEndpointMenu
  - Visible only in local (development) environment
  - Input is a BASE URL (e.g. http://localhost:3000/) used only for debugging replay logic
  - Validations: must be http/https, must be a valid URL, must end with '/'
  - DEBUG PURPOSE ONLY
*/

const isLocalRuntime = () => {
  if (typeof window === 'undefined') return false; // SSR safeguard
  return ['localhost', '127.0.0.1'].includes(window.location.hostname);
};

export const LocalEndpointMenu: React.FC = () => {
  const [endpointUrl, setEndpointUrl] = useState('http://localhost:3000/');
  const [statusMsg, setStatusMsg] = useState<string>('');

  if (!isLocalRuntime()) return null; // hidden in non-local envs

  const validateUrl = (url: string): string | null => {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return 'URL must start with http:// or https://';
    }
    if (!url.endsWith('/')) {
      return 'Base URL must end with a trailing /';
    }
    try {
      // Will throw if invalid
      // eslint-disable-next-line no-new
      new URL(url);
    } catch {
      return 'Invalid URL format';
    }
    return null;
  };

  const handleChange = (val: string) => {
    setEndpointUrl(val);
    const err = validateUrl(val);
    setStatusMsg(err ? err : '');
  };

  return (
    <div className="w-full mb-4 p-4 border border-dashed border-gray-400 bg-white/70 rounded shadow-sm">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-gray-800">Debug Replay Base URL</h3>
        <p className="text-xs text-gray-600 leading-snug mt-1">
          Enter a <strong>base URL</strong> (e.g. http://localhost:3000/) used only while developing. This never runs in
          production. The value must include protocol and end with a trailing slash.
        </p>
      </div>
      <div className="flex flex-col gap-2 md:flex-row md:items-center">
        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide md:w-40">Base URL</label>
        <input
          type="text"
          value={endpointUrl}
          onChange={(e) => handleChange(e.target.value)}
          className={`flex-1 px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 ${statusMsg ? 'border-red-400' : ''}`}
          placeholder="http://localhost:3000/"
        />
      </div>
      {statusMsg && <p className="mt-2 text-xs text-red-600">{statusMsg}</p>}
      <p className="mt-2 text-[10px] text-gray-500">Local only. Validation enforced: protocol + trailing slash.</p>
    </div>
  );
};

export default LocalEndpointMenu;
