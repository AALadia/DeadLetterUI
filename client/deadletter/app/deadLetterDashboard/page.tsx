'use client';

import React, { useEffect } from 'react';
import { DeadLetterTable } from '../components/DeadLetterTable';
import { Header } from '../components/Header';
import { useAppContext } from '../contexts/AppContext';
import LocalEndpointMenu from '../components/LocalEndpointMenu';

export default function DeadLetterDashboard() {
  const { user, router } = useAppContext();

  useEffect(() => {
    if (!user) {
      router.push('/');
    }
  }, [user, router]);


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