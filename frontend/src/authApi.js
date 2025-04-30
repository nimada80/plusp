// authApi.js
// Utility to check user authentication status by calling backend /api/auth/user/

export async function fetchUserStatus() {
  const envVars = window.env || {};
  const baseUrl = envVars.REACT_APP_API_BASE_URL || 'http://localhost';
  
  try {
    const res = await fetch(
      `${baseUrl}/api/auth/user/`,
      {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}
