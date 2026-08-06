# Web Reader API

## API Basic Info

| Field | Value |
|-------|-------|
| API ID | `api-ELbWqODdAgNY` |
| Endpoint | `GET https://app-dvtmyuucfs3l-api-ELbWqODdAgNY-gateway.appmiaoda.com/{url}` |
| Authentication Mode | `platform_managed` |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Response Format | `text/plain` (Markdown by default) or `text/event-stream` (SSE streaming) |
| Billing | Free (`enable_billing: false`) |

---

## Request Parameters

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | The full URL of the target web page, encoded with `encodeURIComponent` and appended directly after the Base URL |

### Request Header Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `X-Gateway-Authorization` | string | Yes | Platform-injected auth token, format: `Bearer ${INTEGRATIONS_API_KEY}` |
| `Accept` | string | No | Response type: `text/html` (default, normal response) or `text/event-stream` (enable SSE streaming mode) |
| `X-Return-Format` | string | No | Return format: `markdown` (default) / `html` / `text` / `screenshot` / `pageshot` |
| `X-With-Images-Summary` | boolean | No | Whether to append an image description summary |
| `X-With-Links-Summary` | boolean | No | Whether to append a links summary |
| `X-Target-Selector` | string | No | CSS selector to extract content from specific page elements only |
| `X-Remove-Selector` | string | No | CSS selector to remove specific elements from the result |
| `X-Timeout` | number | No | Page load timeout (seconds) |
| `X-No-Cache` | boolean | No | Set to `true` to disable cache and force re-fetch |

---

## Response Formats

### Normal Response (default, `Accept: text/html`)

HTTP 200, response body is `text/plain` Markdown text containing:

```
Title: Example Domain

URL Source: http://example.com

Markdown Content:
# Example Domain

This domain is for use in illustrative examples in documents...
```

### SSE Streaming Response (`Accept: text/event-stream`)

HTTP 200, response body is an SSE stream where each event carries a partial Markdown text chunk, and a `[DONE]` event is sent at the end:

```
data: # Example Domain

data: This domain is for use in illustrative examples...

data: [DONE]

```

### Response Headers

| Header | Description |
|--------|-------------|
| `Content-Type` | `text/plain; charset=utf-8` or `text/event-stream` |
| `x-usage-tokens` | Number of tokens consumed by this request |
| `cf-cache-status` | Cloudflare cache status |
| `x-amzn-RequestId` | AWS Lambda request ID |

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success; response body is the parsed Markdown text (or SSE stream) |
| 401 | JWT Token missing or invalid |
| 403 | Token valid but target URL is blocked by GFW |
| 429 | Quota exceeded |
| 402 | Insufficient balance |

---

## Generation-Phase Code Examples

### Normal Mode

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

/**
 * Fetches the target web page and returns its content in Markdown format (normal mode).
 * @param targetUrl - The full URL of the target web page
 * @param options - Optional output control parameters
 * @param options.returnFormat - Return format, default is markdown
 * @param options.withImagesSummary - Whether to append an image summary
 * @param options.withLinksSummary - Whether to append a links summary
 * @param options.targetSelector - CSS selector to extract specific elements only
 * @param options.removeSelector - CSS selector to remove specific elements
 * @param options.timeout - Page load timeout (seconds)
 * @param options.noCache - Whether to disable cache
 * @returns The web page's Markdown text content
 */
async function fetchWebPage(
  targetUrl: string,
  options?: {
    returnFormat?: "markdown" | "html" | "text" | "screenshot" | "pageshot";
    withImagesSummary?: boolean;
    withLinksSummary?: boolean;
    targetSelector?: string;
    removeSelector?: string;
    timeout?: number;
    noCache?: boolean;
  }
): Promise<string> {
  const encodedUrl = encodeURIComponent(targetUrl);
  const endpoint =
    `https://app-dvtmyuucfs3l-api-ELbWqODdAgNY-gateway.appmiaoda.com/${encodedUrl}`;

  const headers: Record<string, string> = {
    "X-Gateway-Authorization": `Bearer ${apiKey}`,
  };

  if (options?.returnFormat) headers["X-Return-Format"] = options.returnFormat;
  if (options?.withImagesSummary !== undefined) {
    headers["X-With-Images-Summary"] = String(options.withImagesSummary);
  }
  if (options?.withLinksSummary !== undefined) {
    headers["X-With-Links-Summary"] = String(options.withLinksSummary);
  }
  if (options?.targetSelector) headers["X-Target-Selector"] = options.targetSelector;
  if (options?.removeSelector) headers["X-Remove-Selector"] = options.removeSelector;
  if (options?.timeout !== undefined) headers["X-Timeout"] = String(options.timeout);
  if (options?.noCache) headers["X-No-Cache"] = "true";

  const response = await fetch(endpoint, { method: "GET", headers });

  if (response.status === 401) throw new Error("Authentication failed: JWT Token missing or invalid");
  if (response.status === 403) throw new Error("Target URL is blocked by GFW and cannot be accessed");
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

  return await response.text();
}

const markdown = await fetchWebPage("https://example.com", { withLinksSummary: true });
console.log(markdown);
```

### SSE Streaming Mode

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

/**
 * Fetches the target web page in SSE streaming mode, processing returned Markdown chunks in real time.
 * @param targetUrl - The full URL of the target web page
 * @param onChunk - Callback function invoked each time a content chunk is received
 * @returns The complete Markdown text
 */
async function fetchWebPageSSE(
  targetUrl: string,
  onChunk?: (chunk: string) => void
): Promise<string> {
  const encodedUrl = encodeURIComponent(targetUrl);
  const endpoint =
    `https://app-dvtmyuucfs3l-api-ELbWqODdAgNY-gateway.appmiaoda.com/${encodedUrl}`;

  const response = await fetch(endpoint, {
    method: "GET",
    headers: {
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
      "Accept": "text/event-stream",
    },
  });

  if (response.status === 401) throw new Error("Authentication failed: JWT Token missing or invalid");
  if (response.status === 403) throw new Error("Target URL is blocked by GFW and cannot be accessed");
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  if (!response.body) throw new Error("Response body is empty, cannot read stream");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullContent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (payload === "[DONE]") break;
      if (payload) {
        fullContent += payload;
        onChunk?.(payload);
      }
    }
  }

  return fullContent;
}

// Example: stream-fetch and print in real time
await fetchWebPageSSE("https://example.com", (chunk) => {
  Deno.stdout.write(new TextEncoder().encode(chunk));
});
```

---

## Notes

- **API Key Security**: `INTEGRATIONS_API_KEY` may only be read on the Edge Function server side; it must never be exposed to the frontend.
- **URL Encoding**: The target URL must be encoded with `encodeURIComponent` before being appended to the path to prevent special characters from causing routing errors.
- **GFW Filtering**: Domains blocked by GFW will return 403; this can be controlled via the `filter_gfw` field in the JWT Payload.
- **SSE Mode**: In streaming mode the response is `text/event-stream` and must be handled with streaming reads; you cannot use `await response.text()` directly.
- **Billing**: This API is free (`enable_billing: false`), but call counts are still recorded.
