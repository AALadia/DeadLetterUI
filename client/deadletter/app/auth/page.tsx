
import React from 'react';
import { Box, Typography, Paper, Stack } from '@mui/material';
import getFirebaseKey from '../_utils/getFirebaseKey'
import LoginButton from './LoginButton';


export default function AuthPage() {
    

  return (
    <div>

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
            <LoginButton  />
        </Stack>
      </Paper>
    </Box>
    </div>
  );
}
