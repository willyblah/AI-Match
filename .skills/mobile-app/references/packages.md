# Packages Reference

## On-Demand Packages (install with `pnpm exec expo install <package>`)

### Media

| Package | Purpose |
|---------|---------|
| `expo-image` | High-performance image display with caching, lazy loading, placeholder |
| `expo-image-picker` | Photo library / camera capture |
| `expo-image-manipulator` | Image compression / resize / crop |
| `expo-camera` | Camera preview / barcode scanning |
| `expo-media-library` | Media library access (save photos, list assets) |
| `expo-audio` | Audio playback and recording |
| `expo-video` | Video playback (`expo-av` replacement) |

### Device Capabilities

| Package | Purpose |
|---------|---------|
| `expo-location` | Geolocation |
| `expo-haptics` | Haptic feedback (iOS; Android Chrome on Web only) |
| `expo-clipboard` | Clipboard read/write |
| `expo-device` | Device info (model, OS version) |
| `expo-network` | Network state (connected, type) |
| `expo-screen-orientation` | Screen orientation lock/unlock |
| `expo-splash-screen` | Custom splash screen hold during async init |
| `expo-sensors` | Motion sensors — Pedometer (step count), Accelerometer, Gyroscope (permission-gated) |

### Data & Storage

| Package | Purpose |
|---------|---------|
| `@react-native-async-storage/async-storage` | Key-value storage (non-sensitive) |
| `expo-secure-store` | Encrypted storage for tokens and secrets |
| `expo-file-system` | File operations (download, read, write, delete) |

### System Integration

| Package | Purpose |
|---------|---------|
| `expo-calendar` | Calendar access (empty stub on Web) |
| `expo-contacts` | Contacts access (empty stub on Web) |
| `expo-web-browser` | In-app browser / file preview / file download |
| `expo-auth-session` | OAuth login flows |

### UI Utilities

| Package | Purpose |
|---------|---------|
| `react-native-ui-datepicker` | Cross-platform date/time picker (pure JS, works on Web) |
| `react-native-marked` | Markdown rendering |

### Graphics & Canvas

| Package | Purpose |
|---------|---------|
| `expo-gl` | WebGL canvas / 3D rendering |
| `expo-three` + `three` | Three.js 3D graphics (requires `expo-gl`) |
| `@shopify/react-native-skia` | 2D canvas / path drawing / paint board |
| `react-native-view-shot` | Capture component as exportable image |

## Platform Compatibility Notes

- `expo-calendar`, `expo-contacts`, `expo-media-library`, `expo-file-system` are empty stubs on Web
- `expo-haptics` works only on Android Chrome on Web; full haptics on iOS and Android native

## Native-only → Web Fallback Map

The preview runs on Web. Modules below are NOT auto-handled by react-native-web/devkit and need a `process.env.EXPO_OS === "web"` branch. The native branch stays unchanged.

| Module | Web behavior without a branch | Web fallback (inside `EXPO_OS === "web"`) |
|--------|-------------------------------|-------------------------------------------|
| `react-native-webview` | not stubbed → crashes / red screen | render an `<iframe src=...>`. NOTE: sites with `X-Frame-Options` deny embedding (blank frame is expected); cross-origin in-frame navigation is unavailable |
| `expo-media-library` (save image) | silent no-op stub (granted but saves nothing) | trigger a browser download via `<a download href={url}>` |
| RN `Share` | not stubbed → crashes | feature-detect `navigator.share`; if missing, copy to clipboard. Treat `AbortError` as user-cancel, not an error |
| `expo-secure-store` | not stubbed → throws on call | `localStorage` |
| `expo-video` autoplay | `NotAllowedError` on Web | start `muted`, or use tap-to-play |
| `react-native-view-shot` (`capture`/`captureRef`) | `capture()` calls `findNodeHandle` → throws `findNodeHandle is not supported on web` | capture the target DOM node with `html2canvas` to a data-uri, then `<a download>`. Branch the WHOLE capture chain, not just the save step |
| `@shopify/react-native-skia` (`<Canvas>`) | CanvasKit WASM not loaded → blank screen / crash | load CanvasKit first via `WithSkiaWeb` / `loadSkiaWeb()` before rendering `<Canvas>`; on save, export the Skia snapshot (`makeImageSnapshot()`), NOT the original source URI |