"use client"

import React from 'react'

import { GoogleAuthProvider } from 'firebase/auth';
import { signInWithPopup } from 'firebase/auth';
import { useAppContext } from '../contexts/AppContext';
import serverRequests from '../_lib/serverRequests';
import { Button } from '@mui/material';


const LoginButton = () => {
    const { setUser, firebaseAuth } = useAppContext();
    const handleGoogleLogin = async () => {
    const googleAuthProvider = new GoogleAuthProvider();
    try {
      const result = await signInWithPopup(firebaseAuth, googleAuthProvider);
      const user = await serverRequests.loginWithGoogle(result.user);
      console.log('User logged in:', user);
      setUser(user);
      // You can redirect or store user here
    } catch (error) {
      console.error('Google Sign-in error:', error);
    }
  };
  return (
    <Button variant="contained" onClick={handleGoogleLogin}>
        Login with Google
    </Button>
  )
}

export default LoginButton
