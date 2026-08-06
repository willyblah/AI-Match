# Seedance 2.0 (Doubao) 视频生成 API 参考

## 目录

- [TypeScript 接口定义](#typescript-接口定义)
- [创建任务代码示例](#创建任务代码示例)
- [查询任务代码示例](#查询任务代码示例)
- [轮询等待完成](#轮询等待完成)
- [Edge Function 代理](#edge-function-代理)
- [前端调用示例](#前端调用示例)
- [状态映射与错误处理](#状态映射与错误处理)
- [素材上传处理](#素材上传处理)

---

## TypeScript 接口定义

```typescript
// ==================== 请求类型 ====================

/** content 数组中的文本项 */
interface TextContent {
  type: "text";
  text: string; // 提示词内容
}

/** content 数组中的图片项 */
interface ImageContent {
  type: "image_url";
  image_url: { url: string }; // 支持公网 URL 或 asset://<asset_id>
  role: "reference_image" | "first_frame" | "last_frame";
}

/** content 数组中的音频项 */
interface AudioContent {
  type: "audio_url";
  audio_url: { url: string };
  role: "reference_audio";
}

/** content 数组项联合类型 */
type ContentItem = TextContent | ImageContent | AudioContent;

/** 创建视频任务请求参数 */
interface CreateVideoTaskParams {
  model: "doubao-seedance-2-0-260128" | "doubao-seedance-2-0-fast-260128";
  content: ContentItem[]; // 必须包含至少一个 text 项
  generate_audio?: boolean; // true: 含同步音频, false: 无声
  ratio?: "16:9" | "4:3" | "1:1" | "3:4" | "9:16" | "21:9" | "adaptive";
  duration?: number; // 默认 5, 范围 4-15
  watermark?: boolean; // true: 含水印
  resolution?: "480p" | "720p" | "1080p"; // 默认 720p，1080p 仅标准版支持
}

// ==================== 响应类型 ====================

/** 上游 API 返回的任务对象（无 code/message/data 包装） */
interface VideoTaskResponse {
  id: string; // 任务 ID，如 doubao.p1.cgt-2025******-****
  model: string;
  status: "succeeded" | "processing" | "failed" | "queued";
  content?: {
    video_url?: string; // 视频下载链接（succeeded 时存在）
  };
  usage?: {
    completion_tokens: number;
    total_tokens: number;
  };
  created_at: number; // Unix 时间戳
  updated_at: number;
  seed?: number;
  resolution?: string;
  ratio?: string;
  duration?: number;
  framespersecond?: number;
  service_tier?: string;
  execution_expires_after?: number; // 链接过期时间（秒）
  generate_audio?: boolean;
  draft?: boolean;
}

/** Edge Function 返回给前端的统一格式 */
interface EdgeFunctionResponse {
  code: 0 | number; // 0 表示成功
  message: string;
  data: {
    task_id: string;
    status: "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED";
    video_url?: string; // Supabase Storage 持久化链接
    error?: string; // FAILED 时的错误信息
  };
}
```

---

## 创建任务代码示例

### 1. 文生视频

```typescript
const params: CreateVideoTaskParams = {
  model: "doubao-seedance-2-0-260128",
  content: [
    {
      type: "text",
      text: "一只橘猫在樱花树下打盹，花瓣轻轻落在它身上，阳光透过树叶洒下斑驳光影"
    }
  ],
  generate_audio: false,
  ratio: "16:9",
  duration: 5,
  watermark: false,
  resolution: "720p"
};

const result = await createVideoTask(params);
console.log(result.id); // 任务 ID
```

### 2. 图生视频（首帧）

```typescript
const params: CreateVideoTaskParams = {
  model: "doubao-seedance-2-0-260128",
  content: [
    {
      type: "text",
      text: "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出"
    },
    {
      type: "image_url",
      image_url: { url: "https://example.com/first-frame.png" },
      role: "first_frame" // ⚠️ 必须是 first_frame，不是 reference_image
    }
  ],
  generate_audio: true,
  ratio: "adaptive",
  duration: 5,
  watermark: false
};
```

### 3. 图生视频（首尾帧）

```typescript
const params: CreateVideoTaskParams = {
  model: "doubao-seedance-2-0-260128",
  content: [
    {
      type: "text",
      text: "图中女孩对着镜头说"茄子"，360度环绕运镜"
    },
    {
      type: "image_url",
      image_url: { url: "https://example.com/first.jpg" },
      role: "first_frame"
    },
    {
      type: "image_url",
      image_url: { url: "https://example.com/last.jpg" },
      role: "last_frame" // ⚠️ 必须是 last_frame
    }
  ],
  generate_audio: true,
  ratio: "adaptive",
  duration: 5
};
```

### 4. 多模态创作（图片+音频）

```typescript
const params: CreateVideoTaskParams = {
  model: "doubao-seedance-2-0-fast-260128",
  content: [
    {
      type: "text",
      text: "使用图片1的清新自然风格，配合音频1的背景音乐节奏，制作一段果茶宣传广告..."
    },
    {
      type: "image_url",
      image_url: { url: "https://example.com/pic1.jpg" },
      role: "reference_image"
    },
    {
      type: "image_url",
      image_url: { url: "https://example.com/pic2.jpg" },
      role: "reference_image"
    },
    {
      type: "audio_url",
      audio_url: { url: "https://example.com/bg-music.mp3" },
      role: "reference_audio"
    }
  ],
  generate_audio: true,
  ratio: "16:9",
  duration: 11,
  watermark: false
};
```

### 5. 虚拟人像

```typescript
const params: CreateVideoTaskParams = {
  model: "doubao-seedance-2-0-260128",
  content: [
    {
      type: "text",
      text: "固定机位，近景镜头，清新自然风格。在室内自然光下，图片1中人物面带笑容，向镜头介绍手中的产品。"
    },
    {
      type: "image_url",
      image_url: { url: "asset://asset-20260310022434-wvg96" }, // ⚠️ asset:// 格式
      role: "reference_image"
    }
  ],
  generate_audio: true,
  ratio: "adaptive",
  duration: 5
};
```

---

## 查询任务代码示例

```typescript
/** 查询视频任务状态 */
async function queryVideoTask(taskId: string): Promise<VideoTaskResponse> {
  const apiKey = process.env["INTEGRATIONS_API_KEY"]!;
  
  const response = await fetch(
      `https://app-dvtmyuucfs3l-api-Q9KWPzO1Eg69-gateway.appmiaoda.com/doubao/v3/contents/generations/tasks/${taskId}`,
    {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  return response.json();
}

// 使用示例
const task = await queryVideoTask("doubao.p1.cgt-2025abc123-456");
console.log(task.status); // "succeeded" | "processing" | "failed" | "queued"
console.log(task.content?.video_url); // 视频链接（succeeded 时存在）
```

---

## 轮询等待完成

```typescript
/** 创建任务并轮询等待完成，返回视频 URL */
async function generateVideoAndWait(
  params: CreateVideoTaskParams,
  options?: {
    pollInterval?: number;
    timeoutMs?: number;
    onStatusChange?: (status: string) => void;
  }
): Promise<string> {
  // 1. 创建任务
  const createResult = await createVideoTask(params);
  const taskId = createResult.id;
  
  console.log(`任务已创建: ${taskId}`);

  // 2. 轮询配置
  const POLL_INTERVAL_MS = options?.pollInterval || 7000; // 7 秒
  const TIMEOUT_MS = options?.timeoutMs || 10 * 60 * 1000; // 10 分钟
  const deadline = Date.now() + TIMEOUT_MS;

  // 3. 轮询循环
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    const result = await queryVideoTask(taskId);
    
    options?.onStatusChange?.(result.status);

    if (result.status === "succeeded" && result.content?.video_url) {
      console.log(`视频生成完成: ${result.content.video_url}`);
      return result.content.video_url;
    }
    
    if (result.status === "failed") {
      throw new Error(`视频生成失败: ${JSON.stringify(result)}`);
    }
    
    // queued / processing → 继续轮询
    console.log(`当前状态: ${result.status}，继续等待...`);
  }

  throw new Error(`任务 ${taskId} 超时（${TIMEOUT_MS / 1000 / 60} 分钟未完成）`);
}

// 使用示例
async function main() {
  try {
    const videoUrl = await generateVideoAndWait(
      {
        model: "doubao-seedance-2-0-260128",
        content: [{ type: "text", text: "夕阳下的海滩，波浪轻轻拍打着沙滩" }],
        duration: 5,
        ratio: "16:9"
      },
      {
        onStatusChange: (status) => console.log(`状态更新: ${status}`)
      }
    );
    
    // ⚠️ 必须立即下载！CDN 链接有时效性
    console.log(`视频 URL: ${videoUrl}`);
    // 下一步：使用 curl -L -o video.mp4 "videoUrl" 下载到本地
  } catch (error) {
    console.error("生成失败:", error);
  }
}
```

---

## Edge Function 代理

### Edge Function 完整代码（Deno/Supabase）

```typescript
// supabase/functions/video-generations/index.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

interface CreateRequest {
  model: string;
  content: Array<{
    type: string;
    text?: string;
    image_url?: { url: string };
    audio_url?: { url: string };
    role?: string;
  }>;
  generate_audio?: boolean;
  ratio?: string;
  duration?: number;
  watermark?: boolean;
  resolution?: string;
}

// CORS 配置
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  // 处理 CORS 预检
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!apiKey) {
      throw new Error("INTEGRATIONS_API_KEY not set");
    }

    // 解析前端请求
    const body: CreateRequest = await req.json();

    // 验证 content 数组必须包含 text
    const hasText = body.content.some(item => item.type === "text");
    if (!hasText) {
      return new Response(
        JSON.stringify({ code: 400, message: "content 数组必须包含至少一个 text 项", data: null }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // 验证不支持视频素材
    const hasVideo = body.content.some(item => item.type === "video_url");
    if (hasVideo) {
      return new Response(
        JSON.stringify({ code: 400, message: "当前版本不支持视频素材", data: null }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // 调用上游 API
    const upstreamResponse = await fetch(
      "https://app-dvtmyuucfs3l-api-nYWN4kMJ1v7L-gateway.appmiaoda.com/doubao/v3/contents/generations/tasks",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`,
        },
        body: JSON.stringify(body),
      }
    );

    if (!upstreamResponse.ok) {
      const errorText = await upstreamResponse.text();
      return new Response(
        JSON.stringify({ code: upstreamResponse.status, message: errorText, data: null }),
        { status: upstreamResponse.status, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // 解析上游响应（扁平结构，无 code/message/data 包装）
    const upstreamData = await upstreamResponse.json();

    // ⚠️ 绝对不能直接透传！必须包装为统一格式
    const wrappedResponse = {
      code: 0,
      message: "ok",
      data: {
        task_id: upstreamData.id, // 上游是 id，前端期望 task_id
        status: mapStatus(upstreamData.status), // 必须映射状态值
        video_url: upstreamData.content?.video_url || null,
        error: upstreamData.status === "failed" ? JSON.stringify(upstreamData) : null,
      }
    };

    return new Response(
      JSON.stringify(wrappedResponse),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ code: 500, message: error.message, data: null }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});

/** 状态映射：上游 → 前端/数据库 */
function mapStatus(s: string | undefined | null): string {
  // ⚠️ 防御性处理：上游 status 可能为 undefined（如刚创建的任务）
  if (!s) return "PENDING";
  
  const m: Record<string, string> = {
    // 排队中状态
    queued: "PENDING",
    pending: "PENDING",
    
    // 处理中状态
    processing: "PROCESSING",
    running: "PROCESSING",  // ⚠️ 重要：running 也是处理中，不是失败
    
    // 成功状态
    succeeded: "SUCCESS",
    success: "SUCCESS",
    completed: "SUCCESS",
    
    // 失败状态
    failed: "FAILED",
    error: "FAILED",
    cancelled: "FAILED",
  };
  
  const mapped = m[s.toLowerCase()];
  if (!mapped) {
    console.warn(`未知状态: ${s}，保持 PROCESSING 继续轮询`);
    return "PROCESSING"; // 未知状态保持轮询，不要判失败
  }
  return mapped;
}
  return mapped;
}
  return mapped;
}
```

### 查询任务 Edge Function

```typescript
// supabase/functions/video-generations-query/index.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!apiKey) throw new Error("INTEGRATIONS_API_KEY not set");

    // 从 URL 获取 task_id
    const url = new URL(req.url);
    const taskId = url.pathname.split("/").pop();

    if (!taskId) {
      return new Response(
        JSON.stringify({ code: 400, message: "缺少 task_id", data: null }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // 查询上游
    const upstreamResponse = await fetch(
    `https://app-dvtmyuucfs3l-api-Q9KWPzO1Eg69-gateway.appmiaoda.com/doubao/v3/contents/generations/tasks/${taskId}`,
      {
        headers: { "Authorization": `Bearer ${apiKey}` },
      }
    );

    if (!upstreamResponse.ok) {
      const errorText = await upstreamResponse.text();
      return new Response(
        JSON.stringify({ code: upstreamResponse.status, message: errorText, data: null }),
        { status: upstreamResponse.status, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const upstreamData = await upstreamResponse.json();

    // 视频 URL 转存到 Supabase Storage（如果已完成）
    // ⚠️ 警告：不要同步下载整个视频文件！会导致 Edge Function 超时
    // 正确做法：直接使用上游 URL，或采用异步转存策略
    let persistentUrl = upstreamData.content?.video_url;
    if (upstreamData.status === "succeeded" && persistentUrl) {
      // 方案1：直接使用上游带签名 URL（有效期24小时）
      // persistentUrl = upstreamData.content.video_url;
      
      // 方案2：如需转存，使用异步策略（后台任务、队列等）
      // 绝不能在这里 fetch(videoUrl) 然后 upload 同步阻塞！
    }

    // 包装为统一格式
    const wrappedResponse = {
      code: 0,
      message: "ok",
      data: {
        task_id: upstreamData.id,
        status: mapStatus(upstreamData.status),
        video_url: persistentUrl || null,
        error: upstreamData.status === "failed" ? JSON.stringify(upstreamData) : null,
      }
    };

    return new Response(
      JSON.stringify(wrappedResponse),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ code: 500, message: error.message, data: null }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});

function mapStatus(upstreamStatus: string | undefined | null): string {
  // ⚠️ 防御性处理：上游 status 可能为 undefined（如刚创建的任务）
  if (!upstreamStatus) return "PENDING";
  
  const statusMap: Record<string, string> = {
    "queued": "PENDING",
    "processing": "PROCESSING",
    "succeeded": "SUCCESS",
    "failed": "FAILED",
  };
  return statusMap[upstreamStatus.toLowerCase()] || upstreamStatus.toUpperCase();
}
```

---

## 前端调用示例

### React 组件调用

```typescript
import { useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export function VideoGenerator() {
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [loading, setLoading] = useState(false);

  async function generateVideo() {
    setLoading(true);
    setStatus("PENDING");
    setVideoUrl("");

    try {
      // 1. 创建任务
      const { data: createData, error: createError } = await supabase.functions.invoke(
        "video-generations",
        {
          body: {
            model: "doubao-seedance-2-0-260128",
            content: [{ type: "text", text: prompt }],
            ratio: "16:9",
            duration: 5
          }
        }
      );

      if (createError) throw createError;
      const taskId = createData.data.task_id;

      // 2. 轮询查询（渐进式）
      const startTime = Date.now();
      const poll = async () => {
        const { data: queryData, error: queryError } = await supabase.functions.invoke(
          "video-generations-query",
          { body: { task_id: taskId } }
        );

        if (queryError) throw queryError;

        const { status: taskStatus, video_url } = queryData.data;
        setStatus(taskStatus);

        if (taskStatus === "SUCCESS" && video_url) {
          setVideoUrl(video_url);
          setLoading(false);
          return;
        }

        if (taskStatus === "FAILED") {
          throw new Error(queryData.data.error || "生成失败");
        }

        // 继续轮询
        const elapsed = Date.now() - startTime;
        const interval = elapsed < 30000 ? 3000 : 7000; // 前30秒3秒，之后7秒
        setTimeout(poll, interval);
      };

      poll();

    } catch (error) {
      console.error("生成失败:", error);
      setStatus("FAILED");
      setLoading(false);
    }
  }

  return (
    <div>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="描述你想生成的视频..."
      />
      <button onClick={generateVideo} disabled={loading}>
        {loading ? `生成中... (${status})` : "生成视频"}
      </button>
      {videoUrl && (
        <video src={videoUrl} controls width="100%" />
      )}
    </div>
  );
}
```

### 使用 Supabase Realtime 订阅（所有任务列表组件都必须使用）

```typescript
import { useEffect, useRef } from "react";

/** 订阅单个任务状态变化（生成页面使用） */
export function useVideoTaskRealtime(taskId: string, onUpdate: (data: any) => void) {
  useEffect(() => {
    if (!taskId) return;

    const subscription = supabase
      .channel(`video_task_${taskId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "video_tasks",
          filter: `task_id=eq.${taskId}`
        },
        (payload) => {
          onUpdate(payload.new);
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [taskId, onUpdate]);
}

/** 订阅所有任务状态变化（历史面板、任务列表页使用） */
export function useVideoTasksRealtime(onUpdate: (data: any) => void) {
  useEffect(() => {
    const subscription = supabase
      .channel('video_tasks_all')
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "video_tasks",
        },
        (payload) => {
          onUpdate(payload.new);
        }
      )
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "video_tasks",
        },
        (payload) => {
          onUpdate(payload.new);
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [onUpdate]);
}
```

---

## 状态映射与错误处理

### 状态映射表

| 上游 API 状态 | Edge Function 输出 | 数据库状态 | 前端显示 |
|--------------|-------------------|-----------|---------|
| `queued` | `PENDING` | `PENDING` | 排队中... |
| `processing` | `PROCESSING` | `PROCESSING` | 生成中... |
| `succeeded` | `SUCCESS` | `SUCCESS` | 已完成 |
| `failed` | `FAILED` | `FAILED` | 生成失败 |

### 错误码处理

| HTTP 状态 | 场景 | 处理建议 |
|----------|------|---------|
| `400` | content 格式错误、role 不正确、素材超限 | 检查 content 数组结构和素材限制 |
| `402` | 余额不足 | 提示用户充值 |
| `429` | 配额已用尽 | 提示用户等待配额重置 |
| `500` | 服务器内部错误 | 重试或联系支持 |

### 常见错误示例

```typescript
// ❌ 错误：content 数组缺少 text 项
const badParams = {
  model: "doubao-seedance-2-0-260128",
  content: [
    { type: "image_url", image_url: { url: "..." }, role: "first_frame" }
  ]
  // 缺少 text 项！会返回 400
};

// ❌ 错误：role 使用不当
const badParams2 = {
  content: [
    { type: "text", text: "..." },
    { type: "image_url", image_url: { url: "..." }, role: "reference_image" }
    // 首帧模式应该用 "first_frame"，不是 "reference_image"
  ]
};

// ✅ 正确：首帧模式
const goodParams = {
  content: [
    { type: "text", text: "..." },
    { type: "image_url", image_url: { url: "..." }, role: "first_frame" }
  ]
};
```

---

## 素材上传处理

### 前端上传流程

```typescript
async function uploadAsset(file: File, assetType: "Image" | "Audio") {
  // 1. 上传到 Supabase Storage 获取公网 URL
  const fileName = `${Date.now()}_${file.name}`;
  const { data: uploadData, error: uploadError } = await supabase.storage
    .from("assets")
    .upload(fileName, file);

  if (uploadError) throw uploadError;

  // 2. 获取公网 URL
  const { data: urlData } = supabase.storage
    .from("assets")
    .getPublicUrl(fileName);

  const publicUrl = urlData.publicUrl;

  // 3. 注册为平台素材（可选，如果需要 asset_id）
  const { data: registerData, error: registerError } = await supabase.functions.invoke(
    "assets-upload",
    {
      body: {
        url: publicUrl,
        asset_type: assetType,
        name: file.name
      }
    }
  );

  if (registerError) throw registerError;

  return {
    publicUrl,      // 用于直接传入 content 数组
    assetId: registerData?.data?.id  // 用于 asset:// 格式
  };
}
```

### 素材使用方式对比

| 方式 | 格式 | 适用场景 |
|------|------|---------|
| 直接 URL | `https://...` | 临时使用，不需要复用 |
| 素材 ID | `asset://<asset_id>` | 需要复用、虚拟人像等 |

---

## 完整工作流示例

### Agent 生成期工作流

```typescript
// 1. 准备参数
const params: CreateVideoTaskParams = {
  model: "doubao-seedance-2-0-260128",
  content: [
    { type: "text", text: "夕阳下的海滩，波浪轻轻拍打着沙滩，远处有帆船" }
  ],
  ratio: "16:9",
  duration: 5,
  generate_audio: false,
  watermark: false
};

// 2. 创建并等待完成
const videoUrl = await generateVideoAndWait(params);

// 3. 立即下载（CDN 链接有时效性）
// 使用 Bash 工具执行：
// curl -L -o /tmp/sunset_beach.mp4 "videoUrl"

// 4. 告知用户结果
console.log("视频已生成并保存到 /tmp/sunset_beach.mp4");
```

### 应用生成后工作流

```typescript
// 前端
async function handleGenerate() {
  // 1. 调用 Edge Function 创建任务
  const { data } = await supabase.functions.invoke("video-generations", {
    body: { model, content, ratio, duration }
  });

  const taskId = data.data.task_id;

  // 2. 保存到数据库，触发 Realtime
  await supabase.from("video_tasks").insert({
    id: taskId,
    status: "PENDING",
    prompt: content[0].text
  });

  // 3. 开始轮询
  startPolling(taskId);
}

// 4. Realtime 订阅自动更新 UI
useVideoTaskRealtime(taskId, (task) => {
  if (task.status === "SUCCESS" && task.video_url) {
    setVideoUrl(task.video_url);
  }
});
```
