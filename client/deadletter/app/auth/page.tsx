'use client'

import React from 'react';
import { Box, Button, Typography, Paper, Stack } from '@mui/material';
import { GoogleLogin, googleLogout } from '@react-oauth/google';
import { auth, googleProvider } from '../firebase'; // adjust path
import { signInWithPopup } from 'firebase/auth';

export default function AuthPage() {
  const handleGoogleLogin = async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      console.log('User logged in:', user);
      // You can redirect or store user here
    } catch (error) {
      console.error('Google Sign-in error:', error);
    }
  };

  return (
    <Box
      sx={{
        height: '100vh',
        backgroundColor: '#f5f5f5',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <Paper elevation={3} sx={{ p: 4, width: 350 }}>
        <Stack spacing={3} alignItems="center">
          <Typography variant="h5" fontWeight="bold">
            Welcome to My App
          </Typography>
          <Button variant="contained" onClick={handleGoogleLogin}>
            Login with Google
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
