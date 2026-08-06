# Media Reference

## Image Display

```tsx
import { Image } from "expo-image";

<Image
  className="w-full h-48 rounded-xl object-cover"
  source={{ uri: "https://example.com/photo.jpg" }}
  placeholder={{ blurhash: "LGF5]+Yk^6#M@-5c,1J5@[or[Q6." }}
  transition={200}
/>
```

`expo-image` provides caching, lazy loading, placeholder, blur hash, animated transitions.

## Image Picking (Camera & Gallery)

```tsx
import * as ImagePicker from "expo-image-picker";

// From camera
const takePhoto = async () => {
  const result = await ImagePicker.launchCameraAsync({
    allowsEditing: true,
    quality: 0.8,
  });
  if (!result.canceled) {
    return result.assets[0].uri;
  }
};

// From gallery
const pickImage = async () => {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images"],
    allowsEditing: true,
    quality: 0.8,
  });
  if (!result.canceled) {
    return result.assets[0].uri;
  }
};
```

## Device-Capability Permission Handling (State-Driven, no Alert.alert)

Applies to EVERY permission-gated capability — camera, photo library, location, notifications, AND **motion sensors** (e.g. `expo-sensors` Pedometer for step counting). Declaring the plugin in `app.json` does NOT grant access: always `request…PermissionsAsync()` at runtime, drive a `denied` UI from state, and NEVER `catch` the permission error to silently degrade to `0` / empty data.

```tsx
const [permissionDenied, setPermissionDenied] = useState(false);

const pickImage = async () => {
  const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (status !== "granted") {
    setPermissionDenied(true);
    return;
  }
  // ... proceed with image picking
};

{permissionDenied && (
  <Text className="text-destructive text-sm mt-2">
    Photo library access is required. Please enable it in Settings.
  </Text>
)}
```

Motion sensors follow the same shape: `Pedometer.isAvailableAsync()` → `Pedometer.requestPermissionsAsync()` → subscribe/read step data → render the `denied` UI when not granted. NEVER assume the sensor is permitted just because the plugin is declared.

## Image Compression

Use `expo-image-manipulator` — REQUIRED before uploading. Max upload size: 1 MB.

```tsx
import { manipulateAsync, SaveFormat } from "expo-image-manipulator";

const compressImage = async (uri: string) => {
  const result = await manipulateAsync(
    uri,
    [{ resize: { width: 1080 } }],
    { compress: 0.7, format: SaveFormat.JPEG }
  );
  return result.uri;
};

// Usage: compress before upload
const compressedUri = await compressImage(originalUri);
await uploadImage(compressedUri, "photos", `images/${Date.now()}.jpg`);
```

Recommended defaults:
- General photos: `width: 1080`, `compress: 0.7`
- Avatars/thumbnails: `width: 300`, `compress: 0.6`

## Image Upload to Supabase Storage

Use `expo/fetch + ArrayBuffer` — cross-platform on iOS/Android/Web. ALWAYS pass the **compressed** uri from `compressImage` above: the output is JPEG, so `contentType: "image/jpeg"` is always correct. NEVER derive `contentType` by slicing the extension off the URI — on Web the asset is a `blob:` / `data:` URI with no usable extension, which yields an invalid MIME and a **415** rejection.

```tsx
import { fetch } from "expo/fetch";

const uploadImage = async (uri: string, bucket: string, path: string) => {
  const response = await fetch(uri);
  const arrayBuffer = await response.arrayBuffer();
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, arrayBuffer, { contentType: "image/jpeg" });
  if (error) throw new Error(error.message); // never swallow — surface it
  return data;
};
```

Bucket & path conventions:
- Bucket naming: `<APP_ID>_<BUSINESS_NAME>_images`
- Unique file paths: `images/${Date.now()}_${Math.random().toString(36).slice(2)}.jpg`
- If no login: grant all users upload permission
- If login exists: grant authenticated users/admins upload permission

## Save to Photo Library

`expo-media-library` is a silent no-op stub on Web (it reports `granted` but saves nothing). MUST branch with `process.env.EXPO_OS === "web"` and trigger a browser download instead. On native, if the URI starts with `content://`, normalize it first via `manipulateAsync` before saving.

```tsx
import * as FileSystem from "expo-file-system";
import * as MediaLibrary from "expo-media-library";

const downloadToGallery = async (url: string, filename: string) => {
  if (process.env.EXPO_OS === "web") {
    // media-library is a no-op stub on Web — trigger a browser download
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    return;
  }

  const { status } = await MediaLibrary.requestPermissionsAsync(false, ["photo"]);
  if (status !== "granted") return;

  const localUri = FileSystem.documentDirectory + filename;
  const { uri } = await FileSystem.downloadAsync(url, localUri);
  const asset = await MediaLibrary.createAssetAsync(uri);
  return asset;
};
```

## Passing URIs Between Screens

Use a module-level store — NEVER pass via expo-router URL params:

```tsx
// src/lib/imageStore.ts
let pendingUri: string | null = null;
export const setPendingUri = (uri: string) => { pendingUri = uri; };
export const consumePendingUri = () => { const uri = pendingUri; pendingUri = null; return uri; };

// Before navigate:
setPendingUri(result.assets[0].uri);
router.push("/(app)/edit-photo");
// In target screen on mount:
const uri = consumePendingUri();
```

## expo-video

```tsx
// NEVER auto-load on Web mount — use hasInteracted ref
const hasInteracted = useRef(process.env.EXPO_OS !== "web");
const [showOverlay, setShowOverlay] = useState(process.env.EXPO_OS === "web");

useEffect(() => {
  if (hasInteracted.current) {
    player.replaceAsync({ uri: videoUrl });
    player.play();
  }
}, []);

// Wrap VideoView for Tailwind styles
<View className="w-full aspect-video rounded-xl overflow-hidden">
  <VideoView style={{ flex: 1 }} player={player} />
  {showOverlay && (
    <Pressable
      style={StyleSheet.absoluteFill}
      className="items-center justify-center bg-black/30"
      onPress={() => {
        hasInteracted.current = true;
        setShowOverlay(false);
        player.replaceAsync({ uri: videoUrl });
        player.play();
      }}
    >
      <Text className="text-white text-lg font-semibold">Tap to Play</Text>
    </Pressable>
  )}
</View>
```

**WHY tap-to-play / muted on Web**: browsers block audible or gesture-less autoplay — calling `play()` on Web mount throws `NotAllowedError`. On Web you MUST either start `muted` or gate playback behind a tap (as above).

Player setup idioms:
- The `useVideoPlayer(source, setup)` setup callback runs **once**. Pass a `null` source and `replace`/`replaceAsync` later — the setup does NOT re-run on source change, so don't put per-source logic there.
- Call `play()` on the `readyToPlay`/`playerStatusChange` event, NOT inside the setup callback (the player isn't ready yet at setup time).

Web CORS limitation: if the video URL does not return `Access-Control-Allow-Origin` header, `expo-video` fails silently on Web. Use videos hosted on CORS-enabled CDN.

Demo/placeholder video URL (use this, never fabricate):
`https://miaoda-zhibo.bj.bcebos.com/AppVideo/%E7%A7%92%E5%93%92%E4%BA%A7%E5%93%81%E5%8A%9F%E8%83%BD%E4%BB%8B%E7%BB%8D_%E4%B8%AD%E6%96%87%E7%89%88.mp4`

## app.json Permission Declarations

Permission descriptions MUST be in the user's language (Chinese for Chinese users, English for English users):

```json
{
  "expo": {
    "plugins": [
      ["expo-image-picker", {
        "cameraPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to access the camera to take photos>",
        "photosPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to access the photo library to select images>"
      }],
      ["expo-camera", {
        "cameraPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to use the camera>",
        "microphonePermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to use the microphone>",
        "recordAudioAndroid": true
      }],
      ["expo-location", {
        "locationWhenInUsePermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to access your location while using the app>",
        "isAndroidBackgroundLocationEnabled": false
      }],
      ["expo-media-library", {
        "photosPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to access your photos>",
        "savePhotosPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to save photos to the library>"
      }],
      ["expo-contacts", {
        "contactsPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to access your contacts>"
      }],
      ["expo-calendar", {
        "calendarPermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to access your calendar>"
      }],
      ["expo-audio", {
        "microphonePermission": "<TRANSLATE: Allow $(PRODUCT_NAME) to use the microphone for recording>"
      }]
    ]
  }
}
```

## Location & Haptics Usage

```tsx
// Location — install first: pnpm exec expo install expo-location
import * as Location from "expo-location";

const { status } = await Location.requestForegroundPermissionsAsync();
if (status !== "granted") { /* handle denial */ return; }
const location = await Location.getCurrentPositionAsync({});

// Haptics (iOS enhancement) — install first: pnpm exec expo install expo-haptics
import * as Haptics from "expo-haptics";
Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
```

## Image Upload Detection & Validation

**When to include upload subsystem**: Treat the system as requiring image upload when the user mentions "image", "picture", "photo", "avatar", "banner", "thumbnail", or "upload image/manage pictures". If any DB table contains image fields, or any feature requires uploading/editing/managing images, an upload subsystem MUST be included.

**File validation rules**:
- Maximum upload size: **1 MB** — compress with `expo-image-manipulator` if file exceeds limit
- Supported formats: JPEG, PNG only
- File paths must contain only English letters, numbers, and hyphens

**Upload UX requirements**:
- Provide a clear upload button
- Display upload progress indication during upload
- Notify users on upload success or failure
- If compression was applied, inform the user