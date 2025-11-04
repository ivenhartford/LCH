/**
 * Performance Monitoring Utility
 *
 * Tracks Core Web Vitals and custom performance metrics for the Lenox Cat Hospital application.
 *
 * Core Web Vitals tracked:
 * - LCP (Largest Contentful Paint): Loading performance (< 2.5s good)
 * - FID (First Input Delay): Interactivity (< 100ms good)
 * - CLS (Cumulative Layout Shift): Visual stability (< 0.1 good)
 * - FCP (First Contentful Paint): Initial render (< 1.8s good)
 * - TTFB (Time to First Byte): Server response (< 600ms good)
 *
 * Usage:
 * Import and call initPerformanceMonitoring() in your App.js or index.js
 */

import { getCLS, getFCP, getFID, getLCP, getTTFB } from 'web-vitals';
import logger from './logger';

// Thresholds for Web Vitals (in seconds/units)
const THRESHOLDS = {
  LCP: { good: 2.5, needsImprovement: 4.0 },
  FID: { good: 0.1, needsImprovement: 0.3 },
  CLS: { good: 0.1, needsImprovement: 0.25 },
  FCP: { good: 1.8, needsImprovement: 3.0 },
  TTFB: { good: 0.6, needsImprovement: 1.5 },
};

/**
 * Determine rating based on metric value and thresholds
 */
const getRating = (name, value) => {
  const threshold = THRESHOLDS[name];
  if (!threshold) return 'unknown';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.needsImprovement) return 'needs-improvement';
  return 'poor';
};

/**
 * Format metric value for display
 */
const formatValue = (name, value) => {
  if (name === 'CLS') {
    return value.toFixed(3);
  }
  return `${(value / 1000).toFixed(2)}s`;
};

/**
 * Send metric to analytics (placeholder - integrate with your analytics service)
 */
const sendToAnalytics = (metric) => {
  // In production, send to analytics service (e.g., Google Analytics, Sentry)
  // Example: gtag('event', metric.name, { value: metric.value });

  if (process.env.NODE_ENV === 'development') {
    console.log(`[Performance] ${metric.name}:`, {
      value: formatValue(metric.name, metric.value),
      rating: metric.rating,
      delta: metric.delta,
      id: metric.id,
    });
  }
};

/**
 * Handle Web Vitals metric
 */
const handleMetric = (metric) => {
  const rating = getRating(metric.name, metric.value);
  const enhancedMetric = { ...metric, rating };

  // Log to console in development
  logger.logPerformance(metric.name, {
    value: formatValue(metric.name, metric.value),
    rating,
    delta: metric.delta,
    id: metric.id,
  });

  // Send to analytics
  sendToAnalytics(enhancedMetric);

  // Log warnings for poor metrics
  if (rating === 'poor') {
    logger.warn(`Poor ${metric.name} detected`, {
      value: formatValue(metric.name, metric.value),
      recommendation: getRecommendation(metric.name),
    });
  }
};

/**
 * Get performance improvement recommendations
 */
const getRecommendation = (metricName) => {
  const recommendations = {
    LCP: 'Optimize images, enable compression, use CDN, implement code splitting',
    FID: 'Reduce JavaScript execution time, break up long tasks, use web workers',
    CLS: 'Specify image dimensions, avoid inserting content above existing content, use transform animations',
    FCP: 'Eliminate render-blocking resources, minify CSS, defer non-critical CSS',
    TTFB: 'Optimize server response time, use CDN, implement caching',
  };

  return recommendations[metricName] || 'Review performance best practices';
};

/**
 * Monitor bundle size (development only)
 */
const logBundleSize = () => {
  if (process.env.NODE_ENV === 'development') {
    // Get approximate JavaScript bundle size from loaded scripts
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    let totalSize = 0;

    scripts.forEach(script => {
      if (script.src.includes('localhost') || script.src.includes('/static/')) {
        // In dev, we can't get exact size, but we can log the count
        totalSize++;
      }
    });

    logger.info('Bundle Analysis', {
      scriptCount: totalSize,
      note: 'Run "npm run build" and check build/static/ for production bundle sizes',
    });
  }
};

/**
 * Monitor memory usage (if available)
 */
const logMemoryUsage = () => {
  if (performance.memory) {
    const { usedJSHeapSize, totalJSHeapSize, jsHeapSizeLimit } = performance.memory;

    logger.logPerformance('Memory Usage', {
      used: `${(usedJSHeapSize / 1048576).toFixed(2)} MB`,
      total: `${(totalJSHeapSize / 1048576).toFixed(2)} MB`,
      limit: `${(jsHeapSizeLimit / 1048576).toFixed(2)} MB`,
      usage: `${((usedJSHeapSize / jsHeapSizeLimit) * 100).toFixed(1)}%`,
    });
  }
};

/**
 * Log navigation timing
 */
const logNavigationTiming = () => {
  if (window.performance && window.performance.timing) {
    const timing = window.performance.timing;
    const navigationStart = timing.navigationStart;

    const metrics = {
      'DNS Lookup': timing.domainLookupEnd - timing.domainLookupStart,
      'TCP Connection': timing.connectEnd - timing.connectStart,
      'Server Response': timing.responseEnd - timing.requestStart,
      'DOM Processing': timing.domComplete - timing.domLoading,
      'Page Load': timing.loadEventEnd - navigationStart,
    };

    logger.logPerformance('Navigation Timing', metrics);
  }
};

/**
 * Initialize performance monitoring
 * Call this once when your app starts
 */
export const initPerformanceMonitoring = () => {
  logger.info('Initializing performance monitoring...');

  // Track Core Web Vitals
  getCLS(handleMetric);
  getFID(handleMetric);
  getLCP(handleMetric);
  getFCP(handleMetric);
  getTTFB(handleMetric);

  // Log bundle size in development
  if (process.env.NODE_ENV === 'development') {
    window.addEventListener('load', () => {
      setTimeout(() => {
        logBundleSize();
        logMemoryUsage();
        logNavigationTiming();
      }, 1000);
    });
  }

  // Log memory usage periodically in development
  if (process.env.NODE_ENV === 'development') {
    setInterval(logMemoryUsage, 60000); // Every minute
  }

  logger.info('Performance monitoring initialized', {
    environment: process.env.NODE_ENV,
    vitalsTracking: 'enabled',
  });
};

/**
 * Manual performance mark (for custom metrics)
 *
 * Usage:
 * performanceMark('feature-loaded');
 * // ... some code ...
 * performanceMeasure('feature-loaded', 'feature-complete');
 */
export const performanceMark = (markName) => {
  if (window.performance && window.performance.mark) {
    performance.mark(markName);
    logger.debug(`Performance mark: ${markName}`);
  }
};

/**
 * Manual performance measure
 */
export const performanceMeasure = (startMark, endMark) => {
  if (window.performance && window.performance.measure) {
    try {
      const measureName = `${startMark}-to-${endMark}`;
      performance.measure(measureName, startMark, endMark);

      const measure = performance.getEntriesByName(measureName)[0];
      logger.logPerformance(`Custom Measure: ${measureName}`, {
        duration: `${measure.duration.toFixed(2)}ms`,
      });

      return measure.duration;
    } catch (err) {
      logger.error('Performance measure failed', err);
    }
  }
  return null;
};

/**
 * Get current performance metrics snapshot
 */
export const getPerformanceSnapshot = () => {
  const snapshot = {
    timestamp: new Date().toISOString(),
    navigationTiming: null,
    memory: null,
  };

  if (window.performance && window.performance.timing) {
    const timing = window.performance.timing;
    snapshot.navigationTiming = {
      dnsLookup: timing.domainLookupEnd - timing.domainLookupStart,
      tcpConnection: timing.connectEnd - timing.connectStart,
      serverResponse: timing.responseEnd - timing.requestStart,
      domProcessing: timing.domComplete - timing.domLoading,
      pageLoad: timing.loadEventEnd - timing.navigationStart,
    };
  }

  if (performance.memory) {
    snapshot.memory = {
      usedMB: (performance.memory.usedJSHeapSize / 1048576).toFixed(2),
      totalMB: (performance.memory.totalJSHeapSize / 1048576).toFixed(2),
      limitMB: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2),
    };
  }

  return snapshot;
};

export default {
  initPerformanceMonitoring,
  performanceMark,
  performanceMeasure,
  getPerformanceSnapshot,
};
