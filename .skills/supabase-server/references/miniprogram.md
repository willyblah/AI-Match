# Supabase Backend — WeChat MiniProgram (Taro / weapp)

Mini-program-specific backend rules. General Schema / RLS / Edge Function / Storage guidance is in the main `SKILL.md`.

## RLS — anonymous UUID guard

- For anonymous requests `auth.uid()` returns the string `"anon"` (NOT NULL), which crashes any `auth.uid() = <uuid_column>` comparison in a USING / WITH CHECK clause. Guard it with a role check so the uuid comparison only runs for logged-in users:
  - `USING (is_public = true OR (auth.role() = 'authenticated' AND auth.uid() = user_id))`

## Storage — transfer remote assets in an Edge Function

When a third-party API returns an image/video URL, stream it into Storage inside an Edge Function, validate the content-type, then store the Storage public URL in the DB (never the third-party URL, which may expire):

```typescript
const response = await fetch(imageUrl)
const contentType = response.headers.get('content-type')
// Only allow image/* or video/*
if (!contentType?.startsWith('image/') && !contentType?.startsWith('video/')) {
  throw new Error('Invalid content type')
}
const filePath = `uploads/${crypto.randomUUID()}.jpg`
await supabase.storage.from(bucketName).upload(filePath, response.body!, { contentType })
const { data: urlData } = supabase.storage.from(bucketName).getPublicUrl(filePath)
// store urlData.publicUrl in the database (NOT the third-party URL)
```

## Column Types — integer vs bigint

Use `bigint` for any column that stores `Date.now()` or other Unix millisecond values — millisecond timestamps (~1.78 trillion in 2026) exceed `integer`'s 32-bit max (2,147,483,647) and trigger Postgres error 22003 at INSERT time.

Example: `sort_order bigint NOT NULL DEFAULT 0` paired with `sort_order: Date.now()`.

## QR Code Generation

Generate QR codes in an Edge Function and store the PNG in a `qrcodes` bucket (public read, created in migration SQL); return the public URL to the frontend. The frontend renders `<Image src={url} />` and MUST pair it with a `Taro.scanCode` scan page (see `supabase-client` reference).

```typescript
// supabase/functions/generate-qrcode/index.ts
import QRCode from 'npm:qrcode'
import { createClient } from 'jsr:@supabase/supabase-js@2'

Deno.serve(async (req) => {
  const { text } = await req.json()
  const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!)
  const pngBuffer = await QRCode.toBuffer(text, { type: 'png', width: 300 })
  const filename = `${crypto.randomUUID()}.png`
  await supabase.storage.from('qrcodes').upload(filename, pngBuffer, { contentType: 'image/png' })
  const { data } = supabase.storage.from('qrcodes').getPublicUrl(filename)
  return Response.json({ url: data.publicUrl })
})
```
