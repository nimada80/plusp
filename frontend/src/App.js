import React from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box, ThemeProvider, CssBaseline, Button, IconButton, Tooltip } from '@mui/material';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import rtlPlugin from 'stylis-plugin-rtl';
import { prefixer } from 'stylis';
import theme from './theme';
import Sidebar from './components/Sidebar';
import Login from './components/Login';
import ChannelManagement from './components/ChannelManagement';
import UserManagement from './components/UserManagement';
import RequireAuth from './RequireAuth';

const cacheRtl = createCache({
  key: 'muirtl',
  stylisPlugins: [prefixer, rtlPlugin],
});

function App() {
  // Navigation hook for routing
  const navigate = useNavigate();
  // Location hook to detect current path
  const location = useLocation();
  
  // تابع پاک کردن کنسول
  const clearConsole = () => {
    // استفاده از متد clear اصلی به جای متد بازنویسی شده
    if (window._originalConsole && window._originalConsole.clear) {
      window._originalConsole.clear();
    } else {
      console.clear();
    }
    
    // پیام تأیید با استفاده از متد error (تنها متد فعال)
    console.error('کنسول پاک شد');
  };
  
  // Logout handler: calls logout API and redirects to login page
  const handleLogout = async () => {
    const envVars = window.env || {};
    const baseUrl = envVars.REACT_APP_API_BASE_URL || 'http://localhost';
    
    try {
      const res = await fetch(
        `${baseUrl}/api/auth/logout/`,
        { method: 'POST', credentials: 'include' }
      );
      if (res.ok) navigate('/login');
      else console.error('Logout failed:', res.status);
    } catch (e) {
      console.error('Logout error:', e);
    }
  };

  return (
    <CacheProvider value={cacheRtl}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ display: 'flex', direction: 'rtl' }}>
          {/* Layout visible on all routes except login */}
          {location.pathname !== '/login' && (
            <>
              <AppBar 
                position="fixed" 
                sx={{ 
                  width: `calc(100% - 240px)`,
                  mr: '240px',
                }}
              >
                <Toolbar>
                  <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    پنل مدیریت
                  </Typography>
                  <Tooltip title="پاک کردن کنسول مرورگر">
                    <Button 
                      color="info" 
                      onClick={clearConsole} 
                      sx={{ ml: 1 }}
                    >
                      پاک کردن کنسول
                    </Button>
                  </Tooltip>
                  <Button color="error" onClick={handleLogout}>خروج</Button>
                </Toolbar>
              </AppBar>
              <Sidebar />
            </>
          )}
          {/* Main content area, adjust margin for layout */}
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              mt: location.pathname === '/login' ? 0 : 8,
              ml: location.pathname === '/login' ? 0 : '240px',
            }}
          >
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={
  <RequireAuth>
    <ChannelManagement />
  </RequireAuth>
} />
              <Route path="/channels" element={
  <RequireAuth>
    <ChannelManagement />
  </RequireAuth>
} />
<Route path="/users" element={
  <RequireAuth>
    <UserManagement />
  </RequireAuth>
} />
            </Routes>
          </Box>
        </Box>
      </ThemeProvider>
    </CacheProvider>
  );
}

export default App;
