"use client"

import React, { useEffect } from 'react';
import { useAppContext } from '../contexts/AppContext';

type SnackbarProps = {
    message: string;
    open: boolean;
    duration?: number;
};

const Snackbar: React.FC<SnackbarProps> = () => {
    const { snackbarMessage, openSnackBar, setOpenSnackbar, snackbarType } = useAppContext();
    if (!openSnackBar) return null;

    useEffect(() => {
        const timer = setTimeout(() => setOpenSnackbar(false), 4000);
        return () => clearTimeout(timer);
    }, [openSnackBar, setOpenSnackbar]);

    // Variant styles based on snackbarType
    const variantStyles: Record<string, React.CSSProperties> = {
        success: { background: '#2e7d32' },
        error: { background: '#d32f2f' },
        info: { background: '#1976d2' },
        warning: { background: '#ed6c02' }
    };
    const baseStyle: React.CSSProperties = {
        position: 'fixed',
        bottom: 32,
        left: '50%',
        transform: 'translateX(-50%)',
        color: '#fff',
        padding: '16px 24px',
        borderRadius: 4,
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 9999,
        minWidth: 200,
        textAlign: 'center',
        fontWeight: 500,
        display: 'flex',
        alignItems: 'center',
        gap: 8
    };
    const appliedStyle = { ...baseStyle, ...(variantStyles[snackbarType] || variantStyles.info) };

    return (
        <div
            style={appliedStyle}
            role="alert"
            aria-live={snackbarType === 'error' ? 'assertive' : 'polite'}
        >
            {snackbarMessage}
            <button
                onClick={() => setOpenSnackbar(false)}
                style={{
                    marginLeft: 8,
                    background: 'rgba(255,255,255,0.15)',
                    border: 'none',
                    color: '#fff',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    fontSize: 16,
                    lineHeight: 1,
                    width: 28,
                    height: 28,
                    borderRadius: 4
                }}
                aria-label="Close"
            >
                ×
            </button>
        </div>
    );
};

export default Snackbar;