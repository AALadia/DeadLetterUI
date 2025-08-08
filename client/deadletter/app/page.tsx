'use client';
import AuthPage from "./auth/page";
import { useAppContext } from './contexts/AppContext';
import { useEffect } from 'react';

export default function Home() {
  const { user, router, isAuthLoading } = useAppContext();

  useEffect(() => {
    if (!isAuthLoading && user) {
      router.push('/deadLetterDashboard');
    }
  }, [user, isAuthLoading, router]);

  if (isAuthLoading) return <div className="p-4 text-sm">Loading...</div>;

  if (user) return null; // redirecting

  return (
    <div>
        <AuthPage />
    </div>
  );
}
