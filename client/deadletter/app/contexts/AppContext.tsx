'use client';

import { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import { User } from '../schemas/UserSchema';
import { useRouter } from 'next/navigation';
import { initializeApp } from "firebase/app";
import getFirebaseKey from '../_utils/getFirebaseKey';
import { getAuth } from 'firebase/auth';

type AppContextType = {
  user: User | null;
  setUser: (user: User | null) => void;
  firebaseAuth: ReturnType<typeof getAuth>;
  router: ReturnType<typeof useRouter>;
  isAuthLoading: boolean;
  logout: () => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children,firebaseApiKey }: { children: ReactNode,firebaseApiKey: string }) => {

  // FIREBASE

    if (!firebaseApiKey) {
      throw new Error("Firebase API key is not defined");
    }
  const firebaseApp = initializeApp(getFirebaseKey(firebaseApiKey));
  const firebaseAuth = getAuth(firebaseApp);
  

  // STATES
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // ROUTER
  const router = useRouter();

  // HYDRATE USER FROM LOCALSTORAGE
  useEffect(() => {
    try {
      const stored = localStorage.getItem('user');
      if (stored) {
        const parsed: User = JSON.parse(stored);
        setUser(parsed);
      }
    } catch (e) {
      console.warn('Failed to parse stored user', e);
    } finally {
      setIsAuthLoading(false);
    }
  }, []);

  // PERSIST USER
  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
      localStorage.removeItem('access_token');
    }
  }, [user]);

  const logout = () => {
    setUser(null);
    router.push('/');
  };

  // VALUES
  const appContextValues = {
    firebaseAuth,
    router,
    user,
    setUser,
    isAuthLoading,
    logout,
  };

  return (
    <AppContext.Provider value={appContextValues}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default useAppContext;

