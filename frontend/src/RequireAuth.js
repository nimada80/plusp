import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { fetchUserStatus } from './authApi';

function RequireAuth({ children }) {
  const location = useLocation();
  const [checked, setChecked] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    let mounted = true;
    fetchUserStatus().then(user => {
      if (mounted) {
        setAuthenticated(!!user);
        setChecked(true);
      }
    });
    return () => { mounted = false; };
  }, []);

  if (!checked) return null; // Or a loading spinner
  if (!authenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

export default RequireAuth;
