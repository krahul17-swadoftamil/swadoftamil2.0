import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';

const GoogleSignInButton = ({ className = "", postLoginRedirect = null }) => {
  const { googleLogin, setPostLoginRedirectUrl } = useAuth();
  const scriptLoadedRef = useRef(false);

  useEffect(() => {
    // Prevent loading script multiple times
    if (scriptLoadedRef.current || window.google) {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
          callback: handleCredentialResponse,
        });
      }
      return;
    }

    // Load Google Identity Services only once
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      scriptLoadedRef.current = true;
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
          callback: handleCredentialResponse,
          context: 'signin',
          ux_mode: 'popup',
          auto_select: false,
          cancel_on_tap_outside: true,
        });
      }
    };

    return () => {
      // Don't remove script on unmount to prevent re-loading
    };
  }, []);

  const handleCredentialResponse = async (response) => {
    console.log('Google OAuth response:', response);
    if (!response || !response.credential) {
      console.error('Invalid Google OAuth response:', response);
      return;
    }

    try {
      await googleLogin(response.credential);
    } catch (error) {
      console.error('Google login failed:', error);
      // TODO: Add user-friendly error notification
    }
  };

  const handleGoogleSignIn = () => {
    // Set post-login redirect if provided
    if (postLoginRedirect) {
      setPostLoginRedirectUrl(postLoginRedirect);
    }

    // Trigger Google Sign-In with error handling
    if (window.google && window.google.accounts && window.google.accounts.id) {
      try {
        window.google.accounts.id.prompt();
      } catch (error) {
        console.error('Google sign-in prompt failed:', error);
        // Fallback: try to render the button
        window.google.accounts.id.renderButton(
          document.createElement('div'), // Temporary element
          { theme: 'outline', size: 'large' }
        );
      }
    } else {
      console.warn('Google Identity Services not loaded yet');
    }
  };

  return (
    <button
      onClick={handleGoogleSignIn}
      className={`w-full flex items-center justify-center gap-3 px-6 py-3 bg-white text-black rounded-xl font-semibold ${className}`}
      type="button"
    >
      <img src="/google.svg" alt="Google" className="w-5 h-5" />
      Continue with Google
    </button>
  );
};

export default GoogleSignInButton;
