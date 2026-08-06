# alipay-sdk-deno 完整用法示例

> 所有示例统一将 `alipay-sdk-deno.ts` 放入 `supabase/functions/_shared/`；每个 `supabase/functions/<function-name>/index.ts` 均通过 `../_shared/alipay-sdk-deno.ts` 引入。

## 初始化

```typescript
import { AlipaySdk, verifySignatureV3 } from "../_shared/alipay-sdk-deno.ts";

const sdk = new AlipaySdk({
  appId: Deno.env.get("ALIPAY_WEB_APP_ID")!,
  privateKey: Deno.env.get("ALIPAY_WEB_PRIVATE_KEY")!,
  alipayPublicKey: Deno.env.get("ALIPAY_WEB_PUBLIC_KEY")!,
  signType: "RSA2",
  camelcase: true,
});
```

---

## 电脑网站支付下单（pageExec）

> ⚠️ 前端必须用 Blob URL 方式跳转，禁止直接 `window.location.href = redirectUrl`。

```typescript
// Edge Function
const formHtml = await sdk.pageExec("alipay.trade.page.pay", "POST", {
  returnUrl: "https://your-domain.com/success",
  notifyUrl: "https://your-domain.com/api/alipay/notify",
  bizContent: {
    out_trade_no: `ORDER${Date.now()}`,
    product_code: "FAST_INSTANT_TRADE_PAY",
    total_amount: "88.88",
    subject: "商品名称",
  },}, isProduction);

return new Response(JSON.stringify({ formHtml }), {
  headers: { "Content-Type": "application/json" },
});
```

```tsx
// 前端 Blob URL 跳转
const blob = new Blob([data.formHtml], { type: "text/html;charset=utf-8" });
const blobUrl = URL.createObjectURL(blob);
window.location.href = blobUrl;
setTimeout(() => URL.revokeObjectURL(blobUrl), 5000);
```

---

## 交易查询

```typescript
const result = await sdk.exec("alipay.trade.query", {
  bizContent: {
    out_trade_no: "ORDER20240101120000001",
    query_options: ["trade_settle_info"],
  },
});
if (result.code === "10000") {
  console.log("交易状态：", result.tradeStatus);
}
```

---

## 交易退款

```typescript
const result = await sdk.exec("alipay.trade.refund", {
  bizContent: {
    out_trade_no: "ORDER20240101120000001",
    refund_amount: "10.00",
    refund_reason: "正常退款",
    out_request_no: "REFUND20240101120000001",
  },
});
if (result.code === "10000") {
  console.log("退款成功，实退金额：", result.refundFee);
}
```

---

## 退款查询

```typescript
const result = await sdk.exec("alipay.trade.fastpay.refund.query", {
  bizContent: {
    out_trade_no: "ORDER20240101120000001",
    out_request_no: "REFUND20240101120000001",
    query_options: ["refund_detail_item_list"],
  },
});
```

---

## 交易撤销

```typescript
const result = await sdk.exec("alipay.trade.cancel", {
  bizContent: { out_trade_no: "ORDER20240101120000001" },
});
```

---

## 对账单下载地址查询

```typescript
const result = await sdk.exec("alipay.data.dataservice.bill.downloadurl.query", {
  bizContent: { bill_type: "trade", bill_date: "2025-05-01" },
});
if (result.code === "10000") {
  console.log("下载地址：", result.billDownloadUrl);
}
```

---

## 异步通知验签

```typescript
// supabase/functions/alipay-notify/index.ts
import { verifySignatureV3 } from "../_shared/alipay-sdk-deno.ts";

Deno.serve(async (req) => {
  const body = await req.text();
  const params: Record<string, string> = {};
  for (const [k, v] of new URLSearchParams(body)) params[k] = v;

  const signStr = Object.keys(params)
    .filter((k) => k !== "sign" && k !== "sign_type" && params[k] !== "")
    .sort()
    .map((k) => `${k}=${params[k]}`)
    .join("&");

  const verified = await verifySignatureV3(
    signStr, params["sign"] ?? "", Deno.env.get("ALIPAY_WEB_PUBLIC_KEY")!
  );
  if (!verified) return new Response("fail", { status: 200 });

  // trade_status === 'TRADE_SUCCESS' || 'TRADE_FINISHED' 才更新订单
  // 同一 notify_id 需做幂等处理
  console.log("notify_type:", params["notify_type"], "out_trade_no:", params["out_trade_no"]);

  return new Response("success", { status: 200, headers: { "Content-Type": "text/plain" } });
});
```

---

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `ALIPAY_WEB_APP_ID` | Web 应用的支付宝应用 ID |
| `ALIPAY_WEB_PRIVATE_KEY` | Web 应用的应用私钥（PKCS#1 或 PKCS#8） |
| `ALIPAY_WEB_PUBLIC_KEY` | Web 应用的支付宝公钥（应用详情 → 开发设置） |
| 网关 | 三项 `ALIPAY_WEB_*` 变量均存在时自动使用正式网关；否则自动使用沙箱网关 |
