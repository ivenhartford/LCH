# Performance Best Practices - Lenox Cat Hospital

**Last Updated:** 2025-11-04
**Status:** Active Guidelines
**Owner:** Development Team

## Overview

This document outlines performance best practices for the Lenox Cat Hospital frontend application. Following these guidelines ensures optimal user experience, fast load times, and efficient resource utilization.

---

## 📊 Performance Monitoring

### Core Web Vitals

We track the following Core Web Vitals metrics:

| Metric | Description | Good | Needs Improvement | Poor |
|--------|-------------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | Loading performance | ≤ 2.5s | 2.5s - 4.0s | > 4.0s |
| **FID** (First Input Delay) | Interactivity | ≤ 100ms | 100ms - 300ms | > 300ms |
| **CLS** (Cumulative Layout Shift) | Visual stability | ≤ 0.1 | 0.1 - 0.25 | > 0.25 |
| **FCP** (First Contentful Paint) | Initial render | ≤ 1.8s | 1.8s - 3.0s | > 3.0s |
| **TTFB** (Time to First Byte) | Server response | ≤ 600ms | 600ms - 1.5s | > 1.5s |

### Monitoring Setup

Performance monitoring is automatically initialized in `App.js`:

```javascript
import { initPerformanceMonitoring } from './utils/performanceMonitoring';

useEffect(() => {
  initPerformanceMonitoring();
}, []);
```

Metrics are logged to:
- Browser console (development)
- Logger utility (all environments)
- Analytics service (production - configure as needed)

---

## 🎯 Optimization Strategies

### 1. Code Splitting & Lazy Loading

**Status:** ✅ Implemented

All route components use React.lazy() for automatic code splitting:

```javascript
// Good: Route-based code splitting
const Dashboard = lazy(() => import('./components/Dashboard'));
const Clients = lazy(() => import('./components/Clients'));

<Suspense fallback={<LoadingFallback />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/clients" element={<Clients />} />
  </Routes>
</Suspense>
```

**Key Points:**
- Critical routes (Login) loaded immediately
- All other routes lazy-loaded
- Reduces initial bundle size by ~40-60%
- Faster Time to Interactive

### 2. Bundle Size Management

**Monitor bundle sizes regularly:**

```bash
# Build and analyze bundle
npm run build:analyze

# Just analyze existing build
npm run analyze-bundle
```

**Bundle Size Targets:**

| Asset Type | Target | Warning | Critical |
|------------|--------|---------|----------|
| JavaScript | < 250 KB | 250-500 KB | > 500 KB |
| CSS | < 50 KB | 50-100 KB | > 100 KB |
| Total (initial) | < 300 KB | 300-600 KB | > 600 KB |

**Optimization Actions:**
- Remove unused dependencies
- Use tree shaking
- Enable production builds (`npm run build`)
- Compress with gzip/brotli on server
- Use CDN for static assets

### 3. React Query Caching

**Status:** ✅ Implemented

React Query provides automatic caching and reduces unnecessary API calls:

```javascript
// Good: Cached queries with stale time
const { data: clients } = useQuery({
  queryKey: ['clients'],
  queryFn: fetchClients,
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

**Best Practices:**
- Set appropriate `staleTime` for each query
- Use `cacheTime` to control memory usage
- Implement optimistic updates for mutations
- Prefetch data when possible

### 4. Image Optimization

**Guidelines:**

- **Format:** Use WebP with fallbacks
- **Compression:** Compress all images before upload
- **Lazy Loading:** Use native lazy loading
- **Responsive Images:** Serve appropriate sizes
- **Icons:** Use SVG or icon fonts (Material-UI icons)

```jsx
// Good: Lazy loaded images
<img
  src="cat-photo.webp"
  alt="Patient photo"
  loading="lazy"
  width="200"
  height="200"
/>
```

### 5. Component Performance

**React.memo() for expensive components:**

```javascript
// Use memo for components that render frequently with same props
const ExpensiveComponent = React.memo(({ data }) => {
  // Complex rendering logic
  return <div>{/* ... */}</div>;
});
```

**useMemo() for expensive calculations:**

```javascript
// Cache expensive computations
const sortedClients = useMemo(() => {
  return clients.sort((a, b) => a.name.localeCompare(b.name));
}, [clients]);
```

**useCallback() for callback stability:**

```javascript
// Prevent unnecessary re-renders
const handleDelete = useCallback((id) => {
  deleteMutation.mutate(id);
}, [deleteMutation]);
```

### 6. List Virtualization

For long lists (100+ items), implement virtualization:

```bash
npm install react-window
```

```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={clients.length}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      {clients[index].name}
    </div>
  )}
</FixedSizeList>
```

**When to use:**
- Lists with 100+ items
- Tables with many rows
- Infinite scrolling

### 7. Network Optimization

**API Calls:**
- Batch related requests when possible
- Implement request debouncing for search
- Use HTTP/2 or HTTP/3
- Enable compression (gzip/brotli)
- Use CDN for static assets

**Example: Debounced search**

```javascript
import { useDebouncedValue } from '@mantine/hooks';

function SearchComponent() {
  const [search, setSearch] = useState('');
  const [debounced] = useDebouncedValue(search, 300);

  const { data } = useQuery({
    queryKey: ['search', debounced],
    queryFn: () => searchClients(debounced),
    enabled: debounced.length > 0,
  });
}
```

---

## 🔧 Development Guidelines

### Performance Checklist for New Features

Before merging new features, verify:

- [ ] Components use React.lazy() if route-based
- [ ] Lists with 100+ items use virtualization
- [ ] Images are optimized and lazy-loaded
- [ ] API calls are cached appropriately
- [ ] No console.log() statements in production code
- [ ] Bundle size increase is justified
- [ ] Performance metrics haven't regressed

### Code Review Focus

Reviewers should check for:

1. **Unnecessary Re-renders**
   - Missing dependency arrays in useEffect
   - Inline object/array creation in props
   - Missing React.memo() for expensive components

2. **Memory Leaks**
   - Cleanup in useEffect return
   - Event listener removal
   - Timer/interval cleanup
   - AbortController for API calls

3. **Bundle Size Impact**
   - Large dependencies (moment.js → date-fns)
   - Unused imports
   - Duplicate code

---

## 📈 Monitoring & Alerts

### Development Monitoring

In development mode, performance metrics are logged to console:

```
[Performance] LCP: 2.3s (good)
[Performance] FID: 85ms (good)
[Performance] CLS: 0.08 (good)
[Performance] Memory Usage: 45.2 MB / 256 MB (17.6%)
```

### Production Monitoring

**Recommended tools:**

1. **Google Lighthouse** - Automated audits
2. **Chrome DevTools Performance** - Detailed profiling
3. **React DevTools Profiler** - Component performance
4. **Sentry** - Error & performance monitoring
5. **LogRocket** - Session replay

### Setting Up Alerts

Configure alerts for:

- LCP > 4 seconds
- FID > 300ms
- CLS > 0.25
- JavaScript bundle > 500 KB
- Total bundle > 1 MB

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] Run `npm run build` and verify no errors
- [ ] Run `npm run analyze-bundle` and review sizes
- [ ] Test on slow 3G network (Chrome DevTools)
- [ ] Test on low-end device (CPU throttling)
- [ ] Verify all images are optimized
- [ ] Check for console errors/warnings
- [ ] Run Lighthouse audit (target score > 90)
- [ ] Enable server compression (gzip/brotli)
- [ ] Configure CDN caching headers
- [ ] Set up performance monitoring

---

## 🎓 Learning Resources

### Official Documentation
- [Web Vitals](https://web.dev/vitals/)
- [React Performance](https://react.dev/learn/render-and-commit)
- [React Query Performance](https://tanstack.com/query/latest/docs/react/guides/performance)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)

### Performance Tools
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [webpack-bundle-analyzer](https://github.com/webpack-contrib/webpack-bundle-analyzer)
- [React DevTools Profiler](https://react.dev/learn/react-developer-tools)
- [Chrome User Experience Report](https://developers.google.com/web/tools/chrome-user-experience-report)

### Courses & Articles
- [web.dev Performance](https://web.dev/learn-performance/)
- [MDN Performance](https://developer.mozilla.org/en-US/docs/Learn/Performance)
- [Kent C. Dodds - React Performance](https://kentcdodds.com/blog/fix-the-slow-render-before-you-fix-the-re-render)

---

## 📝 Performance Budget

Our performance budget for initial page load:

| Metric | Budget | Current | Status |
|--------|--------|---------|--------|
| JavaScript | 250 KB | TBD | ⏳ |
| CSS | 50 KB | TBD | ⏳ |
| Images | 100 KB | TBD | ⏳ |
| Fonts | 50 KB | TBD | ⏳ |
| **Total** | **450 KB** | **TBD** | ⏳ |
| LCP | < 2.5s | TBD | ⏳ |
| FID | < 100ms | TBD | ⏳ |
| CLS | < 0.1 | TBD | ⏳ |

**Update these values after first production build!**

To measure current values:
```bash
npm run build
npm run analyze-bundle
# Review bundle-analysis.json in build/
```

---

## 🔄 Continuous Improvement

### Monthly Performance Review

Schedule monthly reviews to:

1. Review performance metrics trends
2. Identify bottlenecks
3. Update bundle size targets
4. Audit dependencies for updates
5. Review and update this document

### Performance Regression Prevention

Add to CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Analyze bundle size
  run: |
    npm run build
    npm run analyze-bundle
    # Fail if bundle > threshold
```

---

## 📞 Contact & Support

**Performance Issues:**
- Create issue in GitHub with `performance` label
- Include Lighthouse report
- Include browser and device information

**Questions:**
- Review this document first
- Check React/React Query documentation
- Ask in team Slack #frontend channel

---

**Remember:** Performance is a feature, not an afterthought!

Every millisecond counts for user experience. 🚀
