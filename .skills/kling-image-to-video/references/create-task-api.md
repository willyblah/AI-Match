# Create Image-to-Video Task API

**API ID:** `api-eLMlJj3KJD89`
**Billing:** Enabled — billed per call

---

## Overview

Submit a video-generation task that animates a static image. The API accepts a reference image plus optional prompts, model version, camera movement, motion brush masks, end-frame control, and voice references. Returns immediately with a `task_id`; the video is available only after polling (see `query-task-api.md`).

| Property | Value |
|----------|-------|
| **Endpoint** | `POST https://api-eLMlJj3KJD89@api-singapore.klingai.com/v1/videos/image2video` |
| **Content-Type** | `application/json` |
| **Auth** | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |

### Response example

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "task_id": "abc123xyz",
    "task_status": "submitted",
    "task_info": {
      "external_task_id": "my-custom-id"
    },
    "created_at": 1722769557708,
    "updated_at": 1722769557708
  }
}
```

---

## Parameter Reference

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | string | Yes | Reference image as Base64 string or accessible URL. Supported formats: jpg/jpeg/png, ≤10MB, dimensions ≥300px, aspect ratio 1:2.5~2.5:1. **Do not include the `data:image/xxx;base64,` prefix** |
| `model_name` | string | No | Model version, default `kling-v2-6` (per API APIDOC; note: the upstream source doc lists the default as `kling-v1` — treat `kling-v2-6` as the authoritative default per the APIDOC). Options: `kling-v1`, `kling-v1-5`, `kling-v1-6`, `kling-v2-master`, `kling-v2-1`, `kling-v2-1-master`, `kling-v2-5-turbo`, `kling-v2-6` |
| `image_tail` | string | No | End-frame control image (Base64 or URL), same format requirements as `image`. Mutually exclusive with `dynamic_masks`/`static_mask` and `camera_control` |
| `prompt` | string | No | Positive text prompt, ≤2500 characters. Use `<<<voice_1>>>` syntax to insert voice in the video |
| `negative_prompt` | string | No | Negative text prompt, ≤2500 characters |
| `voice_list` | array | No | List of voice references, up to 2 entries. Format: `[{"voice_id":"xxx"}]`. v2.6+ only |
| `sound` | string | No | Generate sound simultaneously with the video: `on` / `off`. Default: `on` (per API APIDOC; note: the upstream source doc lists the default as `off` — treat `on` as the authoritative default per the APIDOC). v2.6+ only |
| `cfg_scale` | float | No | Flexibility [0, 1], default 0.5. Higher values = stronger prompt relevance. **Not supported in v2.x** |
| `mode` | string | No | Generation mode: `std` (standard) / `pro` (professional, higher quality). Default: `pro` (per API APIDOC; note: the upstream source doc lists the default as `std` — treat `pro` as the authoritative default per the APIDOC) |
| `duration` | string | No | Video duration (seconds): `5` or `10`, default `5` |
| `static_mask` | string | No | Static motion brush mask image (Base64 or URL). Aspect ratio must match `image` |
| `dynamic_masks` | array | No | Dynamic motion brush configuration list, up to 6 groups. Each group contains `mask` (mask image) and `trajectories` (motion trajectory coordinate array, 2–77 points for a 5s video). Mutually exclusive with `image+image_tail` and `camera_control` |
| `dynamic_masks[].mask` | string | No | Dynamic mask image (Base64 or URL); aspect ratio must match `image` |
| `dynamic_masks[].trajectories` | array | No | Motion trajectory coordinate sequence; each point format: `{"x": int, "y": int}`. Coordinate origin is the **bottom-left corner** of the image |
| `camera_control` | object | No | Camera movement control. Mutually exclusive with `image+image_tail` and `dynamic_masks`/`static_mask` |
| `camera_control.type` | string | No | Preset camera movement type: `simple` (custom) / `down_back` / `forward_up` / `right_turn_forward` / `left_turn_forward`. `config` must be empty for any type other than `simple` |
| `camera_control.config` | object | No | Six-axis movement parameters, valid only when `type=simple`. Only one field may be non-zero; range [-10, 10]: `horizontal` (left/right translation) / `vertical` (up/down translation) / `pan` (pitch) / `tilt` (yaw) / `roll` (roll) / `zoom` (focal length) |
| `callback_url` | string | No | Callback URL for task status change notifications |
| `external_task_id` | string | No | User-defined task ID, must be unique per account; can be used for task queries |

### Response Fields

| Field path | Type | Description |
|------------|------|-------------|
| `code` | number | Status code; 0 = success |
| `message` | string | Error message |
| `request_id` | string | System-generated request ID |
| `data.task_id` | string | System-generated task ID for subsequent queries |
| `data.task_status` | string | Task status: `submitted` / `processing` / `succeed` / `failed` |
| `data.task_info.external_task_id` | string | User-defined task ID (if provided) |
| `data.created_at` | number | Task creation time, Unix timestamp (ms) |
| `data.updated_at` | number | Task last-updated time, Unix timestamp (ms) |

---

## Generation-time usage (Agent direct call)

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!; // platform_managed — injected by platform

async function submitImage2VideoTask(params: {
  image: string;
  prompt?: string;
  model_name?: string;
  mode?: "std" | "pro";
  duration?: "5" | "10";
  image_tail?: string;
  negative_prompt?: string;
  cfg_scale?: number;
  voice_list?: { voice_id: string }[];
  sound?: "on" | "off";
  static_mask?: string;
  dynamic_masks?: {
    mask: string;
    trajectories: { x: number; y: number }[];
  }[];
  camera_control?: {
    type: "simple" | "down_back" | "forward_up" | "right_turn_forward" | "left_turn_forward";
    config?: {
      horizontal?: number;
      vertical?: number;
      pan?: number;
      tilt?: number;
      roll?: number;
      zoom?: number;
    };
  };
  callback_url?: string;
  external_task_id?: string;
}): Promise<string> {
  const response = await fetch(
    "https://api-eLMlJj3KJD89@api-singapore.klingai.com/v1/videos/image2video",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(params),
    }
  );

  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  const json = await response.json();
  if (json.code !== 0) throw new Error(`API error ${json.code}: ${json.message}`);
  return json.data.task_id;
}
```

---

## Post-generation usage (in-app via Edge Function)

### Edge Function: `edge-functions/kling-submit-image2video.ts`

```typescript
// edge-functions/kling-submit-image2video.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- Parse client request ---
  let image: string;
  let rest: Record<string, unknown>;
  try {
    const body = await req.json();
    image = body.image;
    if (!image) throw new Error("Missing required parameter: image");
    const { image: _image, ...remaining } = body;
    rest = remaining;
  } catch (e) {
    return new Response(JSON.stringify({ error: (e as Error).message }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- Inject platform key (never expose to client) ---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- Call upstream ---
  const upstream = await fetch(
    "https://api-eLMlJj3KJD89@api-singapore.klingai.com/v1/videos/image2video",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ image, ...rest }),
    }
  );

  // Forward quota/balance errors verbatim
  if (upstream.status === 429 || upstream.status === 402) {
    const errText = await upstream.text();
    return new Response(errText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!upstream.ok) {
    return new Response(
      JSON.stringify({ error: `Upstream error: ${upstream.status}` }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  const data = await upstream.json();
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
```

### Frontend → Edge Function

**Recommended (when supabase client is available):**

```typescript
async function submitKlingImage2Video(params: {
  image: string;
  prompt?: string;
  model_name?: string;
  mode?: "std" | "pro";
  duration?: "5" | "10";
  [key: string]: unknown;
}) {
  const { data, error } = await supabase.functions.invoke("kling-submit-image2video", {
    body: params,
  });
  if (error) throw error;
  if (data.code !== 0) throw new Error(`API error ${data.code}: ${data.message}`);
  return data.data; // { task_id, task_status, ... }
}
```

**Fallback (when supabase client is unavailable):**

```typescript
async function submitKlingImage2Video(params: Record<string, unknown>) {
  const res = await fetch(
    `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/kling-submit-image2video`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }
  );

  if (res.status === 429) {
    const err = await res.json();
    throw new Error(`Quota exceeded: ${err.message ?? res.statusText}`);
  }
  if (res.status === 402) {
    const err = await res.json();
    throw new Error(`Insufficient balance: ${err.message ?? res.statusText}`);
  }
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);

  const json = await res.json();
  if (json.code !== 0) throw new Error(`API error ${json.code}: ${json.message}`);
  return json.data;
}
```
