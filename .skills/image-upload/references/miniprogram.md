<IMAGE_UPLOAD_REQUIREMENTS>
* IMAGE PLATFORM & ARCHITECTURE RULES:
  1. **Mandatory Supabase Storage**
     - All image uploads must use Supabase Storage buckets
     - Buckets must be created using `supabase_apply_migration`
     - **Provision the backend before finishing — a compiling build is NOT a working backend.** Using `uploadToSupabase` requires a real Supabase project: you MUST run `supabase_init` (which fills `TARO_APP_SUPABASE_URL` / `TARO_APP_SUPABASE_ANON_KEY` in `.env`) AND create the bucket via `supabase_apply_migration` before finishing. If `.env` still holds the placeholder `SUPABASE_URL_EXTRACT_FROM_SUPABASE_INIT`, the client points at a bogus URL and uploads fail silently (on the H5 preview a failed upload URL renders as a request to `/undefined`). Do NOT treat an "upload"/"save image" feature as purely client-side.
     - Naming convention: `<BUSINESS_NAME>_images`
     - CRITICAL: Never use mock URLs or local temp paths as final image URLs
     - In WeChat MiniProgram, `tempFilePath` (e.g., `wxfile://tmp_xxx.jpg`) MUST be passed to `uploadToSupabase` — the underlying `supabase-wechat-js` converts it to `wx.uploadFile` internally. Do NOT read the file into ArrayBuffer first.
  2. **Bucket Policies**
     - If no login system: all users must be granted permission to upload images
     - If login system exists: admins must be granted permission to upload images
  3. **File Size & Format**
     - Default maximum upload size: 1 MB (enforced by bucket configuration)
     - If file exceeds limit, trigger automatic compression:
       - Convert images to WEBP format
       - Restrict maximum resolution to 1080p (preserve aspect ratio)
       - Apply quality setting = 0.8 and auto-degrade iteratively until < 1 MB
     - Supported formats: JPEG, PNG, GIF, WEBP, AVIF
     - Filename Rules: Only English letters and numbers allowed

* ADDITIONAL FRONTEND INTEGRATION RULES:
  - Design clear **Upload Button**
  - Display **upload progress bar** in real-time
  - Notify users explicitly on **upload success** or **failure**
  - If compression is applied, inform user and display final file size

* FILE UPLOAD IMPLEMENTATION GUIDELINES:
  1. **Use the scaffold utility `src/utils/upload.ts`**
     The scaffold provides three ready-to-use functions:
     - `selectMediaFiles(options)` — select images/videos via `Taro.chooseMedia`, returns `MiniProgramFileInput[]` (weapp) or `File[]` (H5)
     - `selectMessageFile(options)` — select documents / audio / any non-image-non-video file (pdf, docx, mp3, wav, m4a, aac, zip...) from WeChat chat (weapp) or system file picker (H5)
     - `uploadToSupabase(file, { bucket, userId })` — cross-platform upload to Supabase Storage, returns `{ success, data, error }`

  2. **Image Display**
     - **Weapp**: use `tempFilePath` directly as preview before upload (`<Image src={file.tempFilePath} />`)
     - **H5**: upload immediately on file selection, then use the Supabase public URL for preview (`supabase.storage.from(bucket).getPublicUrl(path).data.publicUrl`)
     - After upload (both platforms): display with `<Image src={publicUrl} mode="aspectFit" />`

  3. **`uploadToSupabase` returns a storage path, not a URL** — `data.path` is a relative path like `userId/filename.jpg`. Always store `path` in the database.
     - Whenever the path needs to leave the frontend (image display, passing to an Edge Function, calling an external API), convert it first: `supabase.storage.from(bucket).getPublicUrl(data.path).data.publicUrl`

  4. **Store the full file object in state, not just the path string**
     - Store the entire object returned by `selectMediaFiles` (e.g. `useState<MiniProgramFileInput | File | null>`)
     - Pass it directly to `uploadToSupabase` — do NOT reconstruct a new object from `tempFilePath` alone, as this loses `name` and `type`, causing `application/octet-stream` MIME errors

  5. **DO NOT use deprecated `Taro.chooseImage`** — always use `selectMediaFiles` from `src/utils/upload.ts`

  6. **Video upload uses the SAME `selectMediaFiles`** — call it with `{ mediaType: ['video'] }`. Do NOT hand-write an inline `Taro.chooseMedia` for videos.
     - If you must call `Taro.chooseMedia` directly, `maxDuration` MUST be within **3–60 seconds** (WeChat hard limit). Out-of-range values such as `300` throw `chooseMedia:fail error maxDuration` and the picker never opens — the upload button appears to do nothing.
     - `maxDuration` only caps the length of videos recorded live via camera; it does NOT restrict picking longer existing videos from the album.
     - Video buckets need video MIME types (e.g. `video/mp4`, `video/quicktime`, `video/x-msvideo`) and a larger `file_size_limit` than image buckets.

  7. **Audio (and any non-image/video file) MUST use `selectMessageFile`, NOT `selectMediaFiles`/`chooseMedia`** — `Taro.chooseMedia` only supports `image`/`video`/`mix`; it has NO audio option. Select audio with `selectMessageFile({ type: 'file', extension: ['mp3','wav','m4a','aac','ogg','flac'] })`.
     - Do NOT hack `selectMediaFiles({ mediaType: ['video'] })` to grab audio: it cannot list `.mp3` files, and any `.mp4` the user picks comes in as **`video/mp4`**, which an audio-only bucket rejects with `415 invalid_mime_type`.
     - Weapp constraint: `chooseMessageFile` can only pick files already in a WeChat chat (forward the file to a chat / 文件传输助手 first). Weapp has NO API to read the phone's local music library directly — the product must accept this, or use recording (`getRecorderManager`) instead.

* FILE DOWNLOAD & DOCUMENT PREVIEW (applies to ANY file type — image / audio / video / zip / pdf / docx / xlsx / ...):
  - **CRITICAL — always branch on `Taro.getEnv()`.** The mini-program is also run as an H5 preview (e.g. `*.sandbox.qa.medo.dev`), so any download/preview MUST implement the Weapp AND the H5 path. **Never use `Taro.downloadFile` in H5 for ANY file**: Taro's H5 polyfill hardcodes `xhr.withCredentials = true`, and a credentialed request is rejected by the browser whenever the response carries `Access-Control-Allow-Origin: *` — which Supabase Storage public buckets always return. It fails with `blocked by CORS policy: ... wildcard '*' ... credentials mode is 'include'`, silently breaking download on H5 while it still works on Weapp.
  1. **Download any file to the device**
     - **Weapp**: `Taro.downloadFile({ url })` → check `statusCode === 200` → `res.tempFilePath` (then `Taro.saveFile` / `Taro.openDocument` / preview as the file type needs)
     - **H5**: use a native anchor (no XHR → no credentials → no CORS): create `<a>` with `href=url`, `download=fileName`, `target=_blank`, `click()`, then remove it. Only if you must rename a cross-origin file, `fetch(url)` **without credentials** → `response.blob()` → `URL.createObjectURL(blob)` → `<a download=fileName>` → `click()` → `revokeObjectURL`.
  2. **Preview / open a document (pdf / docx / xlsx / ppt)**
     - **Weapp**: `Taro.downloadFile({ url })` → `statusCode === 200` → `Taro.openDocument({ filePath: res.tempFilePath, fileType: 'pdf' | 'docx' | ..., showMenu: true })`
     - **H5**: `window.open(url, '_blank')` (the browser renders or downloads natively)
  3. **Note**: `selectMessageFile` returns filename (unlike `selectMediaFiles`) — store and use it for the download filename
</IMAGE_UPLOAD_REQUIREMENTS>
