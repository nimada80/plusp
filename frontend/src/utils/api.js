/**
 * apiFetch
 * Wraps fetch to include CSRF token and handle network/API errors.
 * @param {string} url - API endpoint path
 * @param {object} options - fetch options including method, headers, body
 * @returns {object|null} JSON response or null
 * @throws {Error} on HTTP or parsing error
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost';

// Helper to read CSRF token cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export const apiFetch = async (url, options = {}) => {
  const defaultOptions = {
    headers: { 
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    credentials: 'include',
    mode: 'cors',
  };
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };
  
  // Attach CSRF token only for mutation operations
  const csrfToken = getCookie('csrftoken');
  if (csrfToken && ['POST', 'PUT', 'DELETE'].includes(mergedOptions.method)) {
    mergedOptions.headers['X-CSRFToken'] = csrfToken;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, mergedOptions);

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`خطای API: ${url} (${response.status})`);
      try {
        const errorJson = JSON.parse(errorBody);
        throw new Error(`خطا در ارتباط با سرور: ${response.status} - ${errorJson.detail || errorJson.message || response.statusText}`);
      } catch (e) {
        throw new Error(`خطا در ارتباط با سرور: ${response.status} ${response.statusText}`);
      }
    }

    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
      const rawText = await response.text();
      
      try {
        data = JSON.parse(rawText);
      } catch (e) {
        console.error(`خطای تجزیه JSON در ${url}`);
        data = null;
      }
    } else {
      data = await response.text();
    }

    return data;
  } catch (err) {
    console.error(`خطای شبکه: ${url}`);
    throw err;
  }
}; 