#!/usr/bin/env node

/**
 * Bundle Size Analyzer
 *
 * Analyzes the production build bundle sizes and provides recommendations.
 * Run this script after `npm run build` to see bundle statistics.
 *
 * Usage:
 *   npm run analyze-bundle
 *   OR
 *   npm run build:analyze (builds first, then analyzes)
 */

const fs = require('fs');
const path = require('path');

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

// Size thresholds (in KB)
const THRESHOLDS = {
  js: {
    good: 250,
    warning: 500,
    critical: 1000,
  },
  css: {
    good: 50,
    warning: 100,
    critical: 200,
  },
  total: {
    good: 300,
    warning: 600,
    critical: 1200,
  },
};

/**
 * Format bytes to human-readable size
 */
function formatSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * Get color based on size and thresholds
 */
function getColorForSize(sizeKB, type) {
  const threshold = THRESHOLDS[type] || THRESHOLDS.total;

  if (sizeKB <= threshold.good) return colors.green;
  if (sizeKB <= threshold.warning) return colors.yellow;
  return colors.red;
}

/**
 * Get all files in a directory recursively
 */
function getAllFiles(dirPath, arrayOfFiles = []) {
  if (!fs.existsSync(dirPath)) {
    return arrayOfFiles;
  }

  const files = fs.readdirSync(dirPath);

  files.forEach((file) => {
    const fullPath = path.join(dirPath, file);
    if (fs.statSync(fullPath).isDirectory()) {
      arrayOfFiles = getAllFiles(fullPath, arrayOfFiles);
    } else {
      arrayOfFiles.push(fullPath);
    }
  });

  return arrayOfFiles;
}

/**
 * Analyze bundle files
 */
function analyzeBundleFiles(buildDir) {
  const staticDir = path.join(buildDir, 'static');
  const allFiles = getAllFiles(staticDir);

  const filesByType = {
    js: [],
    css: [],
    media: [],
    other: [],
  };

  allFiles.forEach((filePath) => {
    const ext = path.extname(filePath).toLowerCase();
    const stats = fs.statSync(filePath);
    const fileName = path.basename(filePath);
    const relativePath = path.relative(buildDir, filePath);

    const fileInfo = {
      name: fileName,
      path: relativePath,
      size: stats.size,
      sizeKB: stats.size / 1024,
    };

    if (ext === '.js') {
      filesByType.js.push(fileInfo);
    } else if (ext === '.css') {
      filesByType.css.push(fileInfo);
    } else if (['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico'].includes(ext)) {
      filesByType.media.push(fileInfo);
    } else {
      filesByType.other.push(fileInfo);
    }
  });

  return filesByType;
}

/**
 * Calculate totals
 */
function calculateTotals(filesByType) {
  const totals = {};

  Object.keys(filesByType).forEach((type) => {
    const totalSize = filesByType[type].reduce((sum, file) => sum + file.size, 0);
    totals[type] = {
      count: filesByType[type].length,
      size: totalSize,
      sizeKB: totalSize / 1024,
    };
  });

  const allSize = Object.values(totals).reduce((sum, t) => sum + t.size, 0);
  totals.all = {
    count: Object.values(totals).reduce((sum, t) => sum + t.count, 0),
    size: allSize,
    sizeKB: allSize / 1024,
  };

  return totals;
}

/**
 * Print analysis results
 */
function printAnalysis(filesByType, totals) {
  console.log(`\n${colors.bold}${colors.cyan}=== Bundle Size Analysis ===${colors.reset}\n`);

  // Print summary
  console.log(`${colors.bold}Summary:${colors.reset}`);
  console.log(`  Total Files: ${totals.all.count}`);
  console.log(
    `  Total Size: ${getColorForSize(totals.all.sizeKB, 'total')}${formatSize(totals.all.size)}${colors.reset}`
  );
  console.log();

  // Print by type
  ['js', 'css', 'media', 'other'].forEach((type) => {
    if (filesByType[type].length === 0) return;

    const total = totals[type];
    const color = type === 'js' || type === 'css' ? getColorForSize(total.sizeKB, type) : '';

    console.log(`${colors.bold}${type.toUpperCase()} Files (${total.count}):${colors.reset}`);
    console.log(`  Total: ${color}${formatSize(total.size)}${colors.reset}`);

    // Sort by size descending and show top 5
    const sorted = [...filesByType[type]].sort((a, b) => b.size - a.size);
    const topFiles = sorted.slice(0, 5);

    topFiles.forEach((file, index) => {
      const fileColor = type === 'js' || type === 'css' ? getColorForSize(file.sizeKB, type) : '';
      console.log(`    ${index + 1}. ${file.name}: ${fileColor}${formatSize(file.size)}${colors.reset}`);
    });

    if (sorted.length > 5) {
      console.log(`    ... and ${sorted.length - 5} more files`);
    }

    console.log();
  });

  // Print recommendations
  printRecommendations(totals);
}

/**
 * Print performance recommendations
 */
function printRecommendations(totals) {
  console.log(`${colors.bold}${colors.cyan}Recommendations:${colors.reset}\n`);

  const recommendations = [];

  // JavaScript bundle size
  if (totals.js.sizeKB > THRESHOLDS.js.critical) {
    recommendations.push({
      severity: 'critical',
      message: `JavaScript bundle is very large (${formatSize(totals.js.size)})`,
      actions: [
        'Review and remove unused dependencies',
        'Implement code splitting for large components',
        'Use dynamic imports for routes',
        'Enable tree shaking',
        'Consider lazy loading heavy libraries',
      ],
    });
  } else if (totals.js.sizeKB > THRESHOLDS.js.warning) {
    recommendations.push({
      severity: 'warning',
      message: `JavaScript bundle could be optimized (${formatSize(totals.js.size)})`,
      actions: ['Review code splitting opportunities', 'Analyze bundle with webpack-bundle-analyzer'],
    });
  } else {
    recommendations.push({
      severity: 'good',
      message: `JavaScript bundle size is good (${formatSize(totals.js.size)})`,
      actions: [],
    });
  }

  // CSS bundle size
  if (totals.css.sizeKB > THRESHOLDS.css.critical) {
    recommendations.push({
      severity: 'critical',
      message: `CSS bundle is very large (${formatSize(totals.css.size)})`,
      actions: ['Remove unused CSS', 'Consider CSS-in-JS for component styles', 'Enable CSS minification'],
    });
  } else if (totals.css.sizeKB > THRESHOLDS.css.warning) {
    recommendations.push({
      severity: 'warning',
      message: `CSS bundle could be optimized (${formatSize(totals.css.size)})`,
      actions: ['Review CSS for duplicates and unused styles'],
    });
  } else {
    recommendations.push({
      severity: 'good',
      message: `CSS bundle size is good (${formatSize(totals.css.size)})`,
      actions: [],
    });
  }

  // Print recommendations
  recommendations.forEach((rec) => {
    let icon, color;
    if (rec.severity === 'critical') {
      icon = '✗';
      color = colors.red;
    } else if (rec.severity === 'warning') {
      icon = '⚠';
      color = colors.yellow;
    } else {
      icon = '✓';
      color = colors.green;
    }

    console.log(`${color}${icon} ${rec.message}${colors.reset}`);

    if (rec.actions.length > 0) {
      rec.actions.forEach((action) => {
        console.log(`  - ${action}`);
      });
    }

    console.log();
  });

  // General recommendations
  console.log(`${colors.bold}General Optimizations:${colors.reset}`);
  console.log('  - Enable gzip/brotli compression on server');
  console.log('  - Implement service worker for caching');
  console.log('  - Use CDN for static assets');
  console.log('  - Optimize images (use WebP, lazy loading)');
  console.log('  - Monitor bundle size in CI/CD pipeline\n');
}

/**
 * Main function
 */
function main() {
  const buildDir = path.join(__dirname, '..', 'build');

  if (!fs.existsSync(buildDir)) {
    console.error(`${colors.red}Error: Build directory not found at ${buildDir}${colors.reset}`);
    console.error('Please run "npm run build" first.\n');
    process.exit(1);
  }

  console.log(`Analyzing bundle at: ${buildDir}\n`);

  const filesByType = analyzeBundleFiles(buildDir);
  const totals = calculateTotals(filesByType);

  printAnalysis(filesByType, totals);

  // Save report to file
  const reportPath = path.join(buildDir, 'bundle-analysis.json');
  const report = {
    timestamp: new Date().toISOString(),
    buildDir,
    filesByType,
    totals,
  };

  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`${colors.green}Report saved to: ${reportPath}${colors.reset}\n`);
}

// Run the analyzer
main();
