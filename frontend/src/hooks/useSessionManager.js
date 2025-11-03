import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { portalFetch } from '../utils/portalApi';
import { updateLastActivity, clearPortalAuth } from '../utils/portalAuth';

/**
 * Session Manager Hook
 *
 * Manages client portal session with:
 * - 8-hour session timeout (requires full re-login)
 * - 15-minute idle timeout (requires PIN)
 * - Automatic activity tracking
 * - Session state checking
 */
export function useSessionManager() {
  const [showPinSetup, setShowPinSetup] = useState(false);
  const [showPinUnlock, setShowPinUnlock] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const navigate = useNavigate();
  const checkIntervalRef = useRef(null);

  /**
   * Check session status with backend
   */
  const checkSession = useCallback(async () => {
    try {
      const response = await portalFetch('/check-session', {
        method: 'GET',
      });

      if (response.ok) {
        const data = await response.json();

        if (data.session_expired || data.requires_login) {
          // Session expired - require full login
          setSessionExpired(true);
          clearPortalAuth();
          navigate('/portal/login');
        } else if (data.requires_pin && data.has_pin) {
          // Idle timeout - require PIN
          setShowPinUnlock(true);
        } else if (data.requires_pin && !data.has_pin) {
          // Idle timeout but no PIN set - force logout
          clearPortalAuth();
          navigate('/portal/login');
        }
      } else if (response.status === 401) {
        // Unauthorized - session invalid
        clearPortalAuth();
        navigate('/portal/login');
      }
    } catch (error) {
      console.error('Session check failed:', error);
    }
  }, [navigate]);

  /**
   * Handle user activity (mouse, keyboard, etc.)
   */
  const handleActivity = useCallback(() => {
    updateLastActivity();
  }, []);

  /**
   * Handle successful PIN unlock
   */
  const handlePinUnlock = useCallback(() => {
    setShowPinUnlock(false);
    updateLastActivity();
  }, []);

  /**
   * Handle session expiry during PIN unlock
   */
  const handleSessionExpired = useCallback(() => {
    setShowPinUnlock(false);
    setSessionExpired(true);
    clearPortalAuth();
    navigate('/portal/login');
  }, [navigate]);

  /**
   * Set up session checking and activity tracking
   */
  useEffect(() => {
    // Track activity on various events
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];

    events.forEach((event) => {
      window.addEventListener(event, handleActivity);
    });

    // Update activity immediately
    updateLastActivity();

    // Check session status every 30 seconds
    checkIntervalRef.current = setInterval(checkSession, 30000);

    // Check immediately
    checkSession();

    // Cleanup
    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });

      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [handleActivity, checkSession]);

  return {
    showPinSetup,
    setShowPinSetup,
    showPinUnlock,
    setShowPinUnlock,
    sessionExpired,
    handlePinUnlock,
    handleSessionExpired,
  };
}
