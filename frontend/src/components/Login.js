/*
 * Login.js
 * React component rendering a login form.
 * Handles submission of credentials and session initiation via API.
 */

import React, { useState } from 'react';
import { Avatar, TextField, Button, Box, Typography, Paper } from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';

// Login component: renders login form and manages user input
const Login = () => {
  // استفاده از window.env به جای process.env
  const envVars = window.env || {};
  console.log('REACT_APP_API_BASE_URL:', envVars.REACT_APP_API_BASE_URL);
  const baseUrl = envVars.REACT_APP_API_BASE_URL || 'http://localhost';
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  /**
   * handleSubmit
   * Sends POST /api/auth/login/ with username and password.
   * On success, navigates to home; on error, displays message.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    const url = `${baseUrl}/api/auth/login/`;
    console.log('Login URL:', url);
    try {
      const res = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      console.log('Response status:', res.status);
      if (res.ok) {
        navigate('/');
      } else {
        const rawText = await res.text();
        console.error('Raw response:', rawText);
        let data;
        try {
          data = await res.json();
        } catch (parseErr) {
          console.error('JSON parse error:', parseErr);
        }
        setError(data?.error || 'Login failed');
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      <Paper
        elevation={3}
        sx={{ p: 4, width: 360, maxWidth: '100%', borderRadius: 2 }}
      >
        {/* Application title */}
        <Typography variant="h3" align="center" sx={{ fontWeight: 'bold', mb: 2 }}>
          Plus PTT
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
            <LockOutlinedIcon />
          </Avatar>
          <Typography component="h1" variant="h5">
            ورود به پنل مدیریت
          </Typography>
        </Box>
        <form onSubmit={handleSubmit} noValidate>
          <TextField
            label="نام کاربری"
            variant="outlined"
            fullWidth
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            label="رمز عبور"
            type="password"
            variant="outlined"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ mb: 2 }}
          />
          {error && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          <Button type="submit" variant="contained" fullWidth>
            ورود
          </Button>
        </form>
      </Paper>
    </Box>
  );
};

export default Login;
