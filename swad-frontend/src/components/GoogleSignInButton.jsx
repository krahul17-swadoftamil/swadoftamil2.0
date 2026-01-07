import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { auth } from '../firebase';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';

const GoogleSignInButton = ({ className = "", postLoginRedirect = null, rememberMe = false }) => {
  const { firebaseLogin, setPostLoginRedirectUrl, loading } = useAuth();
  const [isInitializing, setIsInitializing] = useState(false);

  const handleGoogleSignIn = async () => {
    try {
      setIsInitializing(true);

      // Track social login attempt
      if (window.gtag) {
        window.gtag('event', 'social_login_attempt', {
          method: 'google',
          remember_me: rememberMe
        });
      }

      // Set post-login redirect if provided
      if (postLoginRedirect) {
        setPostLoginRedirectUrl(postLoginRedirect);
      }

      // Firebase Google sign in
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);

      // Get the ID token
      const idToken = await result.user.getIdToken();

      // Send to backend
      await firebaseLogin(idToken, rememberMe);

      // Track successful login
      if (window.gtag) {
        window.gtag('event', 'login', {
          method: 'google'
        });
      }
    } catch (error) {
      console.error('Firebase Google login failed:', error);
      // Track failed login
      if (window.gtag) {
        window.gtag('event', 'social_login_failed', {
          method: 'google',
          error: error.message
        });
      }
      // TODO: Add user-friendly error notification
    } finally {
      setIsInitializing(false);
    }
  };

  return (
    <button
      onClick={handleGoogleSignIn}
      disabled={loading || isInitializing}
      className={`w-full flex items-center justify-center gap-3 px-6 py-3 bg-white text-black rounded-xl font-semibold transition-all duration-200 ${
        loading || isInitializing 
          ? 'opacity-70 cursor-not-allowed' 
          : 'hover:bg-gray-50 active:scale-95'
      } ${className}`}
      type="button"
    >
      {(loading || isInitializing) ? (
        <>
          <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
          {loading ? 'Signing in...' : 'Loading...'}
        </>
      ) : (
        <>
          <img src="/google.svg" alt="Google" className="w-5 h-5" />
          Continue with Google
        </>
      )}
    </button>
  );
};

export default GoogleSignInButton;
