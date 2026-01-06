import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function GoogleCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for OAuth parameters in URL
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!code) {
          throw new Error('No authorization code received');
        }

        // The OAuth flow should be handled by the backend
        // For now, we'll redirect to home and let the user know
        // In a full implementation, you'd exchange the code for tokens

        // For development, let's assume the backend has already handled the auth
        // and set the session. We'll check if the user is authenticated.

        // Check if user is authenticated by making a request to /api/auth/customers/me/
        const response = await fetch('/api/auth/customers/me/', {
          credentials: 'include',
        });

        if (response.ok) {
          const customerData = await response.json();
          setUser(customerData);
          navigate('/', { replace: true });
        } else {
          throw new Error('Authentication failed');
        }

      } catch (err) {
        console.error('Google callback error:', err);
        setError(err.message);
        setLoading(false);

        // Redirect to home after a delay
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, setUser]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-app">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-lg">Completing sign in...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-app">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold mb-2">Sign In Failed</h1>
          <p className="text-muted mb-4">{error}</p>
          <p className="text-sm text-muted">Redirecting to home page...</p>
        </div>
      </div>
    );
  }

  return null;
}