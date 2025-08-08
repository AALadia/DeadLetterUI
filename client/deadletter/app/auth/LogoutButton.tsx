'use client'
import {signOut} from 'firebase/auth';
import React from 'react'
import { useAppContext } from '../contexts/AppContext';

const LogoutButton = () => {
    const { firebaseAuth} = useAppContext();
    async function logout() {
        console.log('Logging out...');
        console.log('Firebase Auth:', firebaseAuth);
        const res = await signOut(firebaseAuth);
        console.log('Logout response:', res);
    }

  return (
    <button
            onClick={logout}
            className="px-3 py-1.5 text-xs font-medium bg-red-600 text-white rounded hover:bg-red-700 transition disabled:opacity-50"
          >
            Logout
        </button>
  )
}

export default LogoutButton
