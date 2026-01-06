import { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * Custom hook for OTP authentication with loading states
 */
export function useOTPAuth() {
  const { sendOTP, login, loading, error, clearError } = useAuth();
  const [otpSent, setOtpSent] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');

  const requestOTP = useCallback(async (phone) => {
    try {
      clearError();
      setPhoneNumber(phone);
      await sendOTP(phone);
      setOtpSent(true);
      return { success: true };
    } catch (err) {
      setOtpSent(false);
      return { success: false, error: err.message };
    }
  }, [sendOTP, clearError]);

  const verifyOTP = useCallback(async (otp) => {
    try {
      clearError();
      const result = await login(phoneNumber, otp);
      setOtpSent(false);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, [login, phoneNumber, clearError]);

  const reset = useCallback(() => {
    setOtpSent(false);
    setPhoneNumber('');
    clearError();
  }, [clearError]);

  return {
    requestOTP,
    verifyOTP,
    reset,
    otpSent,
    phoneNumber,
    loading,
    error,
  };
}

/**
 * Custom hook for Google authentication
 */
export function useGoogleAuth() {
  const { googleLogin, loading, error, clearError } = useAuth();

  const authenticateWithGoogle = useCallback(async (credential) => {
    try {
      clearError();
      const result = await googleLogin(credential);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, [googleLogin, clearError]);

  return {
    authenticateWithGoogle,
    loading,
    error,
  };
}

/**
 * Custom hook for profile completion
 */
export function useProfileCompletion() {
  const { completeProfile, loading, error, clearError } = useAuth();

  const completeUserProfile = useCallback(async (phone, name, email) => {
    try {
      clearError();
      const result = await completeProfile(phone, name, email);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, [completeProfile, clearError]);

  return {
    completeUserProfile,
    loading,
    error,
  };
}