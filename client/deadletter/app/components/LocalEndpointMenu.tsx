"use client";
import React, { useState, useEffect } from 'react';
import useAppContext from '../contexts/AppContext';


/*
  LocalEndpointMenu
  - Visible only in local (development) environment
  - Input is a BASE URL (e.g. http://localhost:3000/) used only for debugging replay logic
  - Validations: must be http/https, must be a valid URL, must end with '/'
  - DEBUG PURPOSE ONLY
*/

// Determine if we should show the debug menu. We do this client-side to avoid
// SSR -> CSR mismatch (window undefined during SSR previously hid the component).
const computeIsLocal = () => {
  if (typeof window === 'undefined') return false;
  const host = window.location.hostname;
  if (['localhost', '127.0.0.1'].includes(host)) return true;
  // Allow forcing visibility with an env flag (e.g. NEXT_PUBLIC_FORCE_LOCAL_ENDPOINT=true)
  if (process.env.NEXT_PUBLIC_FORCE_LOCAL_ENDPOINT === 'true') return true;
  // Also consider non-production NODE_ENV as acceptable fallback
  if (process.env.NODE_ENV !== 'production') return true;
  return false;
};

export const LocalEndpointMenu: React.FC = () => {
  const [statusMsg, setStatusMsg] = useState<string>('');
  const [show, setShow] = useState(false);
  const { localEndpointUrl, setLocalEndpointUrl } = useAppContext();

  // Decide visibility after mount
  useEffect(() => {
    setShow(computeIsLocal());
  }, []);

  // Persist the debug URL in localStorage (quality-of-life)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (localEndpointUrl) {
      localStorage.setItem('debugLocalEndpointUrl', localEndpointUrl);
    } else {
      localStorage.removeItem('debugLocalEndpointUrl');
    }
  }, [localEndpointUrl]);

  // Load from storage on first mount if context empty
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!localEndpointUrl) {
      const stored = localStorage.getItem('debugLocalEndpointUrl');
      if (stored) setLocalEndpointUrl(stored);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!show) return null; // hidden outside local / forced contexts

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
    setLocalEndpointUrl(val);
    const err = validateUrl(val);
    setStatusMsg(err ? err : '');
  };

  return (
    <div className="mb-4 p-4 rounded-md shadow-sm border border-dashed" style={{ background: 'var(--surface-alt,#f0f3f7)', borderColor: 'var(--color-border,#d1d5db)' }}>
      <div className="mb-3">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-strong,#1f2937)' }}>Debug Replay Base URL</h3>
        <p className="text-xs leading-snug mt-1" style={{ color: 'var(--color-text-muted,#4b5563)' }}>
          Provide a <strong>base URL</strong> (e.g. http://localhost:3000/) that will be used when replaying messages in local development.
          This component never renders in production unless explicitly forced. Must include protocol and end with a trailing slash.
        </p>
      </div>
      <div className="flex flex-col gap-2 md:flex-row md:items-center">
        <label htmlFor="debug-base-url" className="text-xs font-semibold uppercase tracking-wide md:w-40" style={{ color: 'var(--color-text,#374151)' }}>
          Base URL
        </label>
        <input
          id="debug-base-url"
          type="text"
            // Show placeholder distinctly if empty
          value={localEndpointUrl ?? ''}
          onChange={(e) => handleChange(e.target.value.trimStart())}
          placeholder="http://localhost:3000/"
          spellCheck={false}
          className={`flex-1 px-3 py-2 rounded text-sm bg-white border transition focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent shadow-xs ${statusMsg ? 'border-red-400' : 'border-gray-300'}`}
          style={{ color: 'var(--color-text,#111827)' }}
        />
      </div>
      {statusMsg && (
        <p className="mt-2 text-xs" style={{ color: 'var(--color-danger,#dc2626)' }}>
          {statusMsg}
        </p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <p className="text-[10px]" style={{ color: 'var(--color-text-subtle,#6b7280)' }}>
          Local only. Validation: protocol (http/https) + trailing slash.
        </p>
        {localEndpointUrl && !statusMsg && (
          <span className="badge badge-neutral text-[10px]">Active</span>
        )}
        {!localEndpointUrl && (
          <span className="badge badge-soft text-[10px]">Not Set</span>
        )}
        <button
          type="button"
          onClick={() => handleChange('')}
          className="btn btn-sm btn-ghost text-[10px]"
          title="Clear value"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default LocalEndpointMenu;
