'use client';

import { createContext, useState, useContext, ReactNode, useEffect, use } from 'react';
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
  showSnackbar: (serverResponse: ServerResponseType, duration?: number) => void;
  openSnackBar: boolean;
  setOpenSnackbar: (open: boolean) => void;
  snackbarMessage: string | null;
  setSnackbarMessage: (message: string | null) => void;
  snackbarType: 'success' | 'error';
  localEndpointUrl: string | null;
  setLocalEndpointUrl: (url: string | null) => void;
};

type ServerResponseType = {
  status: number;
  message: string;
  data?: any;
}

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

  // SNACKBAR
  const [openSnackBar,setOpenSnackbar] = useState(false)
  const [snackbarMessage,setSnackbarMessage] = useState<string | null>(null)
  const [snackbarType, setSnackbarType] = useState<'success' | 'error'>('success');

  const showSnackbar = (serverResponse: ServerResponseType, duration: number = 4000) => {
    console.log(serverResponse.message)
    setOpenSnackbar(true)
    setSnackbarType(serverResponse.status === 200 ? 'success' : 'error')
    setSnackbarMessage(serverResponse.message)
  }
  

  // STATES
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [localEndpointUrl, setLocalEndpointUrl] = useState<string | null>(null);

  // ROUTER
  const router = useRouter();

  // VALUES
  const appContextValues = {
    firebaseAuth,
    router,
    user,
    setUser,
    isAuthLoading,
    showSnackbar,
    openSnackBar,
    setOpenSnackbar,
    snackbarMessage,
    setSnackbarMessage,
    snackbarType,
    localEndpointUrl,
    setLocalEndpointUrl
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

