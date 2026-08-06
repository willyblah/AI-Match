# Supabase Frontend — Expo / React Native (App)

## Supabase Client (CRITICAL)

- **NEVER create a new Supabase client file** — the boilerplate already provides one at `src/client/supabase.ts` with correct Expo-native configuration
- ALWAYS import from `@/client/supabase`: `import { supabase } from "@/client/supabase"`
- The pre-built client uses `expo-sqlite/localStorage/install` for session persistence (works on iOS, Android, and Web)
- Reference implementation (do NOT copy — it already exists):

```tsx
import { createClient } from '@supabase/supabase-js'
import 'expo-sqlite/localStorage/install';

const supabaseUrl: string = process.env.EXPO_PUBLIC_SUPABASE_URL
const supabaseAnonKey: string = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: localStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
})
```

### Auth Session strategy (edit the client config, do NOT recreate the file)

The client file is pre-built — make **targeted edits** to it (the `auth` options, and for anonymous apps the top-level `localStorage` import); never recreate `src/client/supabase.ts`.

- **App with login** (uses the `login` skill): keep the defaults above (`persistSession: true`, `autoRefreshToken: true`, `storage: localStorage`).
- **Anonymous App** (NO Supabase auth session at all — uses only the anon key plus a self-managed `device_id`, never calls `signInAnonymously` / `signIn*`): MUST set `persistSession: false` and `autoRefreshToken: false`, and **remove** `storage: localStorage` plus the top-level `import 'expo-sqlite/localStorage/install'`. Always use the anon key.
  - **WHY**: the Web preview is same-origin, so a persisted `localStorage` session is shared across different generated apps ("串号"). A stale session token then fails signature verification (`signature verification failed`, 400/403). A stateless anon client avoids this entirely.
  - **CAVEAT**: if the app DOES call `signInAnonymously()` and ties data to `auth.uid()` via RLS, keep `persistSession: true` — disabling it would mint a new anonymous user on every reload and orphan the prior user's data.

**STRICTLY FORBIDDEN**: AsyncStorage for business data; Web storage APIs (`localStorage` / `sessionStorage`) **for business-data persistence** (auth session storage and platform-fallback storage are exempt — see the platform fallback rules in `mobile-app`).

## Environment Variables

- Prefix: `EXPO_PUBLIC_` (NOT `VITE_`)
- Access: `process.env.EXPO_PUBLIC_SUPABASE_URL` (NOT `import.meta.env`)
- NEVER put secrets in `EXPO_PUBLIC_` variables — they are visible in the built app

## Key Differences from Web Supabase

| Aspect | Web | Expo / RN |
|--------|-----|-----------|
| Env prefix | `VITE_` | `EXPO_PUBLIC_` |
| Env access | `import.meta.env.VITE_XXX` | `process.env.EXPO_PUBLIC_XXX` |
| Auth storage | `localStorage` (browser) | `localStorage` via `expo-sqlite/localStorage/install` |
| Session detect URL | `true` | `false` |
| File upload | `File` / `Blob` | `ArrayBuffer` (fetch + arrayBuffer()) |
| Realtime | Supported | Phase-1 NOT supported |

## Type Definitions

- Define types in `types/types.ts` matching SQL schema

## api.ts Coding Standards

- Encapsulate queries in `db/api.ts`
- Use `.maybeSingle()` instead of `.single()`
- Always use `.order()` with `.limit()`; implement pagination for multiple results
- When writing select queries, avoid `table_name(*)` — use `table_name!foreign_key_name` to explicitly specify relationships
- Return arrays safely: `Array.isArray(data) ? data : []`
- Empty strings need to be converted to NULL to prevent SQL formatting misalignment
- Prefer `.insert()` without `.select()`
- **Strictly prohibit** fetching all data without pagination; prefer cursor-based pagination
- Protect nulls: `meeting.participants?.length`, `meeting.title || 'Untitled'`
- NEVER store images/videos as Base64 in database — use Supabase Storage

## File Upload (CRITICAL — `expo/fetch + ArrayBuffer`, works on iOS / Android / Web)

```tsx
import { fetch } from "expo/fetch";

const uploadFile = async (uri: string, bucket: string, path: string, mimeType: string) => {
  const response = await fetch(uri);
  const arrayBuffer = await response.arrayBuffer();
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, arrayBuffer, { contentType: mimeType });
  if (error) throw new Error(error.message); // never swallow — surface it
  return data;
};
```

- `contentType` correctness (a wrong MIME → **415** rejection):
  - **Images**: compress to JPEG first via `expo-image-manipulator` (see the `mobile-app` skill), then upload with `contentType: "image/jpeg"` — the compressed output is always JPEG.
  - **Other file types**: pass the picker's `asset.mimeType`.
  - NEVER derive the MIME by slicing the file extension off the URI — on Web the picker yields `blob:` / `data:` URIs with no usable extension, producing an invalid MIME. Use `image/jpeg`, never the non-standard `image/jpg`.
- MUST check `error` and throw `error.message` — never swallow the upload error.
- Debugging `signature verification failed`: first reproduce with the anon key via `curl` to isolate "wrong token sent" from a missing bucket / RLS / wrong key.
- Do **not** use `FileReader`, `blob`, or `base64` for uploads
- Frontend validation: 1MB limit, snake_case filenames
- Compress before uploading using `expo-image-manipulator`

## Edge Function Invocation

- Always use `supabase.functions.invoke`
- Read `error.context.text()` for the real error message
- For GET requests with parameters, append query parameters directly to the function name: `supabase.functions.invoke('test-fn?id=123', { method: 'GET' })`

```tsx
const { data, error } = await supabase.functions.invoke('my-function', {
  body: { key: 'value' },
  method: 'POST',
});

if (error) {
  const errorMsg = await error?.context?.text();
  console.error("Edge function error:", errorMsg || error?.message);
}
```

**STRICTLY FORBIDDEN**: Direct third-party API calls from client-side code — all must go through Edge Functions.

## Realtime (low-frequency feature — RN not supported)

Phase-1 does NOT support Supabase Realtime in React Native. Use pull-to-refresh or periodic polling with a configurable interval instead. Full spec in `supabase-server/references/realtime.md`.

## Auth

For login/signup/OAuth/SSO implementation, follow the `login` skill — **MUST** call `skill_action(skill="login")` to get the latest spec.
