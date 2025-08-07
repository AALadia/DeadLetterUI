'use client';

import React from 'react';
import { DeadLetterTable } from '../components/DeadLetterTable';
import { Header } from '../components/Header';
import { RetryAllButton } from '../components/RetryAllButton';

export default function DeadLetterDashboard() {
  return (
    <div className="flex flex-col items-center min-h-screen bg-red-100 p-4">
      <Header />
      <div className="container mx-auto">
        <RetryAllButton />
        <DeadLetterTable />
      </div>
    </div>
  );
}