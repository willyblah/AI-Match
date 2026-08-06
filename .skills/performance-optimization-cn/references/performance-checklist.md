# Performance Checklist

## Pre-Optimization Checklist

- [ ] Baseline measurements recorded (LCP, INP, CLS, bundle size, API response times)
- [ ] Bottleneck identified with profiling data (not assumed)
- [ ] Performance budget defined and documented

## Frontend Optimization Checklist

### Images
- [ ] All images have explicit width and height attributes (prevents CLS)
- [ ] Images below the fold use `loading="lazy"`
- [ ] Modern formats used (AVIF, WebP) with fallbacks
- [ ] Responsive images use `srcset` and `sizes`
- [ ] Images optimized/compressed (no larger than necessary)

### JavaScript
- [ ] Bundle size checked and within budget
- [ ] Code splitting implemented (route-level, heavy components)
- [ ] Dynamic imports used for rarely-used features
- [ ] Tree-shaking verified (no unused code)
- [ ] No `eval()` or `innerHTML` with dynamic content

### CSS
- [ ] Critical CSS inlined (above-the-fold content)
- [ ] Non-critical CSS loaded asynchronously
- [ ] CSS minified and gzipped
- [ ] Unused CSS removed (PurgeCSS or equivalent)

### Rendering
- [ ] No render-blocking resources (CSS/JS deferred)
- [ ] Font loading optimized (`font-display: swap`)
- [ ] Layout thrashing eliminated (no forced reflows)
- [ ] Long tasks broken up (`yieldToMain`, `scheduler`)

### Network
- [ ] HTTP/2 or HTTP/3 enabled
- [ ] Assets served with proper Cache-Control headers
- [ ] DNS-prefetch/preconnect for critical origins
- [ ] Service Worker caching strategy configured (if applicable)

## Backend Optimization Checklist

### Database
- [ ] All queries are parameterized (no string concatenation)
- [ ] N+1 queries eliminated (use joins/includes)
- [ ] Indexes exist for frequently queried columns
- [ ] Pagination implemented for list endpoints
- [ ] Query execution time logged and monitored

### Caching
- [ ] Frequently-read data cached (Redis/memory)
- [ ] HTTP caching headers set correctly
- [ ] Cache invalidation strategy documented
- [ ] No cache stampede risks (thundering herd)

### API Design
- [ ] Response payloads minimized (only necessary fields)
- [ ] Compression enabled (gzip/brotli)
- [ ] Rate limiting configured
- [ ] Timeout set for external service calls

## React-Specific Checklist

- [ ] `React.memo` used for expensive components (not all)
- [ ] `useMemo` used for expensive computations (with dependencies)
- [ ] `useCallback` used for stable function references (when needed)
- [ ] Stable references for objects/arrays passed to children
- [ ] Virtualization for long lists (`react-window`, `react-virtualized`)
- [ ] Debounced/throttled event handlers (scroll, resize, input)

## Monitoring & Regression Prevention

- [ ] Core Web Vitals monitored in production (RUM)
- [ ] Lighthouse CI configured in pipeline
- [ ] Bundle size check in CI (`bundlesize`)
- [ ] Performance regression alerts configured
- [ ] Regular performance audits scheduled (monthly/quarterly)

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Solution |
|-------------|-------------|----------|
| Optimizing without measuring | Wastes time, adds complexity | Profile first, optimize what matters |
| `React.memo` everywhere | Adds overhead, hurts readability | Only for expensive components |
| Loading all data upfront | Slows initial load, wastes bandwidth | Pagination, lazy loading |
| Synchronous heavy computation | Blocks main thread, freezes UI | Web Workers, async processing |
| Unbounded caches | Memory leaks, OOM crashes | TTL, size limits, LRU eviction |
| Missing error boundaries | Crashes take down entire app | React Error Boundaries |

## Quick Commands

```bash
# Bundle analysis
npx webpack-bundle-analyzer dist/stats.json

# Lighthouse CI
npx lhci autorun

# Check bundle size
npx bundlesize

# Profile React renders
# React DevTools Profiler → Record → Analyze

# Check for unused dependencies
npx depcheck

# Analyze package size
npx package-size-limit
```

## Measurement Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| Lighthouse | Synthetic performance audit | CI, pre-release checks |
| Chrome DevTools Performance | Main thread profiling | Interaction jank, long tasks |
| Chrome DevTools Network | Network waterfall | TTFB, resource loading |
| web-vitals | RUM Core Web Vitals | Production monitoring |
| React DevTools Profiler | Component render analysis | React re-render issues |
| webpack-bundle-analyzer | Bundle composition | Bundle bloat investigation |
| Clinic.js | Node.js profiling | Backend bottleneck identification |

## Performance Budget Template

```json
{
  "budgets": [
    {
      "path": "/",
      "resourceSizes": [
        { "resourceType": "script", "budget": 200 },
        { "resourceType": "stylesheet", "budget": 50 },
        { "resourceType": "image", "budget": 500 }
      ],
      "timings": [
        { "metric": "interactive", "budget": 3500 },
        { "metric": "first-contentful-paint", "budget": 1800 },
        { "metric": "largest-contentful-paint", "budget": 2500 }
      ]
    }
  ]
}
```
