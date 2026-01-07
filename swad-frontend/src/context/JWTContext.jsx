import { createContext, useContext, useState, useEffect } from 'react';

const JWTContext = createContext(null);

export function JWTProvider({ children }) {
  const [accessToken, setAccessToken] = useState(localStorage.getItem('access_token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated
  const isAuthenticated = !!accessToken && !!user;

  // Save tokens to localStorage
  useEffect(() => {
    if (accessToken) {
      localStorage.setItem('access_token', accessToken);
    } else {
      localStorage.removeItem('access_token');
    }
  }, [accessToken]);

  useEffect(() => {
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    } else {
      localStorage.removeItem('refresh_token');
    }
  }, [refreshToken]);

  // Login with JWT tokens
  const login = (tokens, userData) => {
    setAccessToken(tokens.access);
    setRefreshToken(tokens.refresh);
    setUser(userData);
  };

  // Logout
  const logout = () => {
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  // Refresh access token
  const refreshAccessToken = async () => {
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/auth/jwt/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh: refreshToken,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAccessToken(data.access);
        return true;
      } else {
        // Refresh token expired, logout
        logout();
        return false;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  };

  // Get valid access token (refresh if needed)
  const getValidAccessToken = async () => {
    if (!accessToken) return null;

    // Check if token is expired (simple check - you might want to decode JWT)
    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      const now = Date.now() / 1000;

      if (payload.exp < now) {
        // Token expired, try to refresh
        const refreshed = await refreshAccessToken();
        if (!refreshed) return null;
      }

      return accessToken;
    } catch (error) {
      console.error('Token validation failed:', error);
      return null;
    }
  };

  // Initialize - check if we have valid tokens
  useEffect(() => {
    const initializeAuth = async () => {
      if (accessToken) {
        const validToken = await getValidAccessToken();
        if (validToken) {
          // TODO: Fetch user data if needed
          // For now, we'll assume the user data is stored in localStorage or fetched separately
        } else {
          logout();
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const value = {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshAccessToken,
    getValidAccessToken,
  };

  return (
    <JWTContext.Provider value={value}>
      {children}
    </JWTContext.Provider>
  );
}

export function useJWT() {
  const context = useContext(JWTContext);
  if (!context) {
    throw new Error('useJWT must be used within a JWTProvider');
  }
  return context;
}