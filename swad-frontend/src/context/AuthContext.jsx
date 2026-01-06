import { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [isGuest, setIsGuest] = useState(false);
  const [postLoginRedirect, setPostLoginRedirect] = useState(
    sessionStorage.getItem("postLoginRedirect")
  );

  /* ======================================================
     SESSION RESTORE
  ====================================================== */

  const restoreSession = useCallback(async () => {
    try {
      setError(null);
      const res = await api.get("/auth/me/");
      setUser(res);
      setIsAuthenticated(true);
    } catch (err) {
      setUser(null);
      setIsAuthenticated(false);
      // Only set error for network issues, not for unauthenticated state
      if (err.message && !err.message.includes('401') && !err.message.includes('403')) {
        setError(err.message);
      }
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  /* ======================================================
     HELPERS
  ====================================================== */

  const mergeGuestToUser = useCallback(() => {
    if (isGuest) {
      setIsGuest(false);
    }
  }, [isGuest]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /* ======================================================
     AUTH ACTIONS
  ====================================================== */

  const sendOTP = useCallback(async (phone) => {
    setLoading(true);
    setError(null);
    try {
      return await api.post("/auth/send-otp/", { phone });
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (phone, otp) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/auth/verify-otp/", {
        phone,
        code: otp,
      });

      setUser(res.customer);
      setIsAuthenticated(true);
      await mergeGuestToUser();

      // Handle post-login redirect
      const redirectUrl = postLoginRedirect || sessionStorage.getItem('postLoginRedirect');
      if (redirectUrl) {
        sessionStorage.removeItem('postLoginRedirect');
        setPostLoginRedirect(null);
        window.location.href = redirectUrl;
      }

      return {
        customer: res.customer,
        isNew: res.is_new_customer,
        is_new_customer: res.is_new_customer,
      };
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [postLoginRedirect, mergeGuestToUser]);

  const completeProfile = useCallback(async (phone, name, email) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/auth/complete-profile/", {
        phone,
        name,
        email,
      });

      setUser(res.customer);
      setIsAuthenticated(true);
      await mergeGuestToUser();

      // Handle post-login redirect
      const redirectUrl = postLoginRedirect || sessionStorage.getItem('postLoginRedirect');
      if (redirectUrl) {
        sessionStorage.removeItem('postLoginRedirect');
        setPostLoginRedirect(null);
        window.location.href = redirectUrl;
      }

      return res;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [postLoginRedirect, mergeGuestToUser]);

  const googleLogin = useCallback(async (credential) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/auth/google-login/", { credential });
      setUser(res.customer);
      setIsAuthenticated(true);
      await mergeGuestToUser();

      // Handle post-login redirect
      const redirectUrl = postLoginRedirect || sessionStorage.getItem('postLoginRedirect');
      if (redirectUrl) {
        sessionStorage.removeItem('postLoginRedirect');
        setPostLoginRedirect(null);
        window.location.href = redirectUrl;
      }

      return res;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [postLoginRedirect, mergeGuestToUser]);

  const logoutUser = useCallback(async () => {
    setLoading(true);
    try {
      await api.post("/auth/logout/");
    } catch (err) {
      // Logout should succeed even if the API call fails
      console.warn('Logout API call failed:', err);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsGuest(false);
      setError(null);
      sessionStorage.removeItem("postLoginRedirect");
      setLoading(false);
    }
  }, []);

  /* ======================================================
     GUEST + REDIRECT SUPPORT
  ====================================================== */

  const enableGuestCheckout = useCallback(() => {
    setIsGuest(true);
  }, []);

  const setPostLoginRedirectUrl = useCallback((url) => {
    sessionStorage.setItem("postLoginRedirect", url);
    setPostLoginRedirect(url);
  }, []);

  /* ======================================================
     COMPUTED VALUES (MEMOIZED)
  ====================================================== */

  const contextValue = useMemo(() => ({
    user,
    checking,
    isAuthenticated,
    isGuest,
    error,
    loading,

    isAdmin: Boolean(user?.is_staff || user?.is_superuser),
    isStaff: Boolean(user?.is_staff),

    sendOTP,
    login,
    completeProfile,
    googleLogin,
    logoutUser,

    enableGuestCheckout,
    setPostLoginRedirectUrl,
    clearError,
  }), [
    user,
    checking,
    isAuthenticated,
    isGuest,
    error,
    loading,
    postLoginRedirect,
    sendOTP,
    login,
    completeProfile,
    googleLogin,
    logoutUser,
    enableGuestCheckout,
    setPostLoginRedirectUrl,
    clearError,
  ]);

  /* ======================================================
     PROVIDER
  ====================================================== */

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/* ======================================================
   HOOK
====================================================== */

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
