# Query Image-to-Video Task API

**API ID:** `api-rLobzpqX85m9`
**Billing:** Disabled (query calls are free)

---

## Overview

Query the status and result of a previously submitted image-to-video generation task. Returns the current task status and, when complete, the array of generated video URLs. Because the URLs are ephemeral (30-day TTL), the Edge Function implementation automatically transfers videos to Supabase Storage before returning.

| Property | Value |
|----------|-------|
| **Endpoint** | `GET https://api-rLobzpqX85m9@api-singapore.klingai.com/v1/videos/image2video/{id}` |
| **Content-Type** | `application/json` |
| **Auth** | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |

The `{id}` path segment must be replaced with either `task_id` (system-generated) or `external_task_id` (user-defined). Do not provide both.

### Response example (task succeeded)

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "task_id": "abc123xyz",
    "task_status": "succeed",
    "task_status_msg": "",
    "task_info": {
      "external_task_id": "my-custom-id"
    },
    "created_at": 1722769557708,
    "updated_at": 1722769601234,
    "task_result": {
      "videos": [
        {
          "id": "video-id-001",
          "url": "https://p1.a.kwimgs.com/bs2/upload-ylab-stunt/.../output.mp4",
          "duration": "5"
        }
      ]
    }
  }
}
```

---

## Parameter Reference

### Request Parameters (Path)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Conditionally required | System-generated task ID (replace `{id}` in the path directly). Use either this or `external_task_id` |
| `external_task_id` | string | Conditionally required | User-defined task ID (replace `{id}` in the path directly). Use either this or `task_id` |

### Response Fields

| Field path | Type | Description |
|------------|------|-------------|
| `code` | number | Status code; 0 = success |
| `message` | string | Error message |
| `request_id` | string | System-generated request ID |
| `data.task_id` | string | System task ID |
| `data.task_status` | string | Task status: `submitted` / `processing` / `succeed` / `failed` |
| `data.task_status_msg` | string | Failure reason when task status is `failed` |
| `data.task_info.external_task_id` | string? | User-defined task ID (if provided) |
| `data.created_at` | number | Task creation time, Unix timestamp (ms) |
| `data.updated_at` | number | Task last-updated time, Unix timestamp (ms) |
| `data.task_result.videos` | array? | List of generated videos (only present when status is `succeed`) |
| `data.task_result.videos[].id` | string | Globally unique video ID |
| `data.task_result.videos[].url` | string | Video CDN URL (valid for 30 days) |
| `data.task_result.videos[].duration` | string | Video duration (seconds) |

---

## Generation-time usage (Agent direct call)

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!; // platform_managed — injected by platform

async function queryImage2VideoTask(taskId: string): Promise<{
  task_status: string;
  task_status_msg?: string;
  task_result?: { videos: { id: string; url: string; duration: string }[] };
}> {
  const response = await fetch(
    `https://api-rLobzpqX85m9@api-singapore.klingai.com/v1/videos/image2video/${taskId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
    }
  );

  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  const json = await response.json();
  if (json.code !== 0) throw new Error(`API error ${json.code}: ${json.message}`);
  return json.data;
}
```

---

## Post-generation usage (in-app via Edge Function)

The query Edge Function fetches the task status from Kling, and — when the video is ready — immediately transfers it to Supabase Storage so the URL returned to the client is persistent (no 30-day expiry risk).

### Edge Function: `edge-functions/kling-query-image2video.ts`

```typescript
// edge-functions/kling-query-image2video.ts
import { serve } from "https://deno.land/std/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

/**
 * Stream a remote video directly into Supabase Storage.
 */
async function streamVideoToStorage(
  videoUrl: string,
  bucketName: string
): Promise<{ success: true; publicUrl: string } | { success: false; error: string }> {
  try {
    new URL(videoUrl); // validate format

    const response = await fetch(videoUrl);
    if (!response.ok) {
      throw new Error(`Fetch failed: ${response.status} ${response.statusText}`);
    }

    const contentType = response.headers.get("content-type") ?? "video/mp4";
    const ext = contentType.split("/")[1]?.split(";")[0] ?? "mp4";
    const filePath = `uploads/${crypto.randomUUID()}.${ext}`;

    const { data, error } = await supabase.storage
      .from(bucketName)
      .upload(filePath, response.body!, { contentType, cacheControl: "no-cache", upsert: false });

    if (error) throw error;

    const { data: urlData } = supabase.storage.from(bucketName).getPublicUrl(data.path);
    return { success: true, publicUrl: urlData.publicUrl };
  } catch (err) {
    return { success: false, error: (err as Error).message };
  }
}

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- Parse client request ---
  let taskId: string;
  try {
    const body = await req.json();
    taskId = body.task_id ?? body.external_task_id;
    if (!taskId) throw new Error("Missing task_id or external_task_id");
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
    `https://api-rLobzpqX85m9@api-singapore.klingai.com/v1/videos/image2video/${taskId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
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

  const responseData = await upstream.json();

  // --- Transfer video URLs to Supabase Storage when task succeeds ---
  if (
    responseData.code === 0 &&
    responseData.data?.task_status === "succeed" &&
    responseData.data?.task_result?.videos?.length > 0
  ) {
    const videos = responseData.data.task_result.videos as {
      id: string;
      url: string;
      duration: string;
    }[];

    const transferredVideos = await Promise.all(
      videos.map(async (video) => {
        const transfer = await streamVideoToStorage(video.url, "generated-media");
        return {
          ...video,
          url: transfer.success ? transfer.publicUrl : video.url,
          // If transfer fails, fall back to the original ephemeral URL and log
          ...(transfer.success ? {} : { _transfer_error: transfer.error }),
        };
      })
    );

    responseData.data.task_result.videos = transferredVideos;
  }

  return new Response(JSON.stringify(responseData), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
```

### Frontend → Edge Function

**Recommended (when supabase client is available):**

```typescript
async function queryKlingImage2Video(taskId: string) {
  const { data, error } = await supabase.functions.invoke("kling-query-image2video", {
    body: { task_id: taskId },
  });
  if (error) throw error;
  if (data.code !== 0) throw new Error(`API error ${data.code}: ${data.message}`);
  return data.data; // { task_status, task_result: { videos: [...] }, ... }
}
```

**Fallback (when supabase client is unavailable):**

```typescript
async function queryKlingImage2Video(taskId: string) {
  const res = await fetch(
    `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/kling-query-image2video`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
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

---

## Notes

- **Video expiry**: Upstream CDN links expire after 30 days. The Edge Function automatically transfers videos to Supabase Storage on task success and returns a persistent URL. If transfer fails, it falls back to the original URL and attaches a `_transfer_error` field in the response.
- **Supabase Storage bucket**: The Edge Function uses a bucket named `generated-media`. Ensure this bucket is created in your Supabase project with appropriate public-access policies (or adjust as needed).
- **Polling frequency**: Poll every 7 seconds. Set a polling timeout of 10 minutes.
