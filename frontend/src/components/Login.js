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
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  /**
   * handleSubmit
   * Sends POST /api/auth/login/ with username and password.
   * On success, navigates to home; on error, displays message.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const url = `${baseUrl}/api/auth/login/`;
    console.log('Login URL:', url);
    
    try {
      const res = await fetch(url, {
        method: 'POST',
        credentials: 'include', // مهم برای انتقال کوکی‌ها
        mode: 'cors', // تصریح که این درخواست CORS است
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ username, password }),
      });
      
      console.log('Response status:', res.status);
      console.log('Response headers:', Object.fromEntries([...res.headers.entries()]));
      
      // حتی اگر پاسخ OK باشد، اما خطایی در تبدیل به JSON باشد، آن را مدیریت کنیم
      const rawText = await res.text();
      console.log('Raw response:', rawText);
      
      let data = null;
      try {
        // اگر متن خالی نباشد، سعی کنیم آن را به JSON تبدیل کنیم
        if (rawText && rawText.trim()) {
          data = JSON.parse(rawText);
        }
      } catch (parseErr) {
        console.error('JSON parse error:', parseErr);
      }
      
      if (res.ok) {
        // اگر لاگین موفق بود، به صفحه اصلی برویم
        navigate('/');
      } else {
        // در غیر این صورت، پیام خطا نمایش دهیم
        setError(data?.error || `Login failed (${res.status}): ${res.statusText}`);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError(`Connection error: ${err.message}`);
    } finally {
      setLoading(false);
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
            autoComplete="username"
            inputProps={{ dir: "rtl" }}
            disabled={loading}
          />
          <TextField
            label="رمز عبور"
            type="password"
            variant="outlined"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ mb: 2 }}
            autoComplete="current-password"
            inputProps={{ dir: "rtl" }}
            disabled={loading}
          />
          {error && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          <Button 
            type="submit" 
            variant="contained" 
            fullWidth
            disabled={loading}
          >
            {loading ? 'درحال ورود...' : 'ورود'}
          </Button>
        </form>
      </Paper>
    </Box>
  );
};

export default Login;
