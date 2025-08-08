'use client';

import React, { useEffect } from 'react';
import { DeadLetterTable } from '../components/DeadLetterTable';
import { Header } from '../components/Header';
import { useAppContext } from '../contexts/AppContext';
import LocalEndpointMenu from '../components/LocalEndpointMenu';

export default function DeadLetterDashboard() {
  const { user, router, isAuthLoading } = useAppContext();

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/');
    }
  }, [user, isAuthLoading, router]);

  if (isAuthLoading) {
    return <div className="p-6 text-sm">Loading...</div>;
  }

  if (!user) {
    return null; // redirect in effect
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-red-100 p-4 w-full">
      <Header />
      <div className="container mx-auto w-full">
        <LocalEndpointMenu />
        <DeadLetterTable />
      </div>
    </div>
  );
}