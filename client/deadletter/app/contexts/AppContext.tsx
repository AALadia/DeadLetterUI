'use client';

import { createContext, useState, useContext, ReactNode } from 'react';
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

  // ROUTER
  const router = useRouter();

  // FUNCTIONS

  const appContextValues = {
    firebaseAuth,
    router,
    user,
    setUser,
  }

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

