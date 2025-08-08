'use client';

import { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import { User } from '../schemas/UserSchema';
import { useRouter } from 'next/navigation';
import { initializeApp } from "firebase/app";
import getFirebaseKey from '../_utils/getFirebaseKey';
import { getAuth,onAuthStateChanged } from 'firebase/auth';
import serverRequests from '../_lib/serverRequests';

type AppContextType = {
  user: User | null;
  setUser: (user: User | null) => void;
  firebaseAuth: ReturnType<typeof getAuth>;
  router: ReturnType<typeof useRouter>;
  isAuthLoading: boolean;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children,firebaseApiKey }: { children: ReactNode,firebaseApiKey: string }) => {

  // FIREBASE

    if (!firebaseApiKey) {
      throw new Error("Firebase API key is not defined");
    }
  const firebaseApp = initializeApp(getFirebaseKey(firebaseApiKey));
  const firebaseAuth = getAuth(firebaseApp);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(firebaseAuth, (user) => {
        // User is signed in, you can get user details here
        if (user) {
          serverRequests.loginWithGoogle(user).then((userData) => {
            console.log('User data from server:', userData);
            setUser(userData.data);
            localStorage.setItem('access_token', userData?.access_token || '');
            router.push('/deadLetterDashboard'); // Redirect to dashboard after login
          })
      } else {
        // User is signed out
        setUser(null);
        localStorage.removeItem('access_token');
        router.push('/'); // Redirect to home or login page
      }
    });
    return () => unsubscribe()
    }, [firebaseAuth]);

  
  

  // STATES
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // ROUTER
  const router = useRouter();

  // VALUES
  const appContextValues = {
    firebaseAuth,
    router,
    user,
    setUser,
    isAuthLoading,
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

