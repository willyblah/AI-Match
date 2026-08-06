<APP_PAYMENT_REQUIREMENTS>
Design Principles:
1. **IMPORTANT**: Think minimal pages, complete flow for payment (and refund if required).
    - Analyze user requirements to determine the MINIMAL page set needed for complete workflow
    - MUST ensure workflow is complete and closed-loop, but avoid unnecessary pages
2. Required items > User requirements > Recommended items.
3. Orders modified only by edge functions with a server role. User-level permissions prohibited.
4. **NO PLACEHOLDER PAGES**: No TODO items—all payment code must be production-complete. NO placeholder content.
5. Idempotency: Use optimistic locking (`UPDATE ... WHERE status = 'pending'`), check affected rows > 0 before triggering business logic. 0 rows = duplicate callback → skip logic, return SUCCESS.
6. Transaction atomicity: Operations in same TX must succeed or fail together.
7. **Secrets NEVER in client code**: ALL signing, verification, and callback handling MUST be in Edge Functions. Client only invokes Edge Functions and polls for results.
8. **Server-side pricing**: Client sends `product_id` + `quantity`, NEVER sends `amount`. Edge Function calculates the price.
9. **No openid required**: Unlike MiniProgram (JSAPI), App payment does NOT require user openid.
10. **Trigger Conditions**:
    - **Refund trigger**: Do NOT implement refund if user only asks for payment/purchase functionality

Edge Functions to create and deploy:
1. `create_app_payment` — Create App prepay order, return invocation params (prepay_id + secondary signature)
2. `app_payment_callback` — Handle WeChat async payment callback, verify signature + update order status
3. `query_order_status` — Client polls order payment result
4. `refund_order` — Create refund request (only if refund required)
5. `app_refund_callback` — Handle WeChat refund result callback (only if refund required)

<PAYMENT_REQUIREMENTS>
Required Items (Payment):
1. Frontend: payment button → call `create_app_payment` Edge Function → receive invocation params → call WeChat OpenSDK to launch payment → navigate to result page → poll `query_order_status`.
2. Orders must be associated with the purchaser (use `auth.uid()` from Supabase auth).
3. **create_app_payment** (TX1):
   - Validate purchaser info
   - Look up product price, calculate total
   - [TX1] Inventory freeze (if applicable) + order save (status='pending')
   - Call WeChat **APP prepay API** (post-TX1): `POST /v3/pay/transactions/app`
   - Assemble client invocation params with **secondary signature**
   - Return invocation params: `{appId, partnerId, prepayId, nonceStr, timeStamp, package, sign}`
   - WeChat fail = order remains pending (auto-cancel by timeout)
4. **app_payment_callback** (TX2):
   - Decrypt + verify payment (check: trade_state='SUCCESS', amount matches order)
   - [TX2] Order update (pending→paid) + inventory convert (reserved→sold, if applicable)
   - **State change**: UPDATE MUST constrain current state in WHERE clause (`WHERE status = 'pending'`)
   - **Idempotency**: Check affected rows. 0 = duplicate callback (skip logic, return SUCCESS). >0 = first callback (execute logic)
   - Return SUCCESS for duplicate callbacks or successful updates. Return FAIL only for retriable errors
5. **query_order_status**: Simple GET endpoint, query order by `order_no`, return current status. Client polls every 2s, max 30s.
6. Use WeChat Pay **APP API** exclusively. Secrets (exact names, configured via Plugin Center): MERCHANT_ID, MERCHANT_APP_ID, MCH_CERT_SERIAL_NO, MCH_PRIVATE_KEY, WECHAT_PAY_PUBLIC_KEY_ID, WECHAT_PAY_PUBLIC_KEY, MCH_API_V3_KEY
7. If secrets are missing or WeChat API fails: frontend must display detailed error prompting user to check configuration.
8. Utility functions below must be used unmodified.

```typescript
// create_app_payment Edge Function
import Wechatpay, { Formatter, Rsa } from "npm:wechatpay-axios-plugin@0.9.4";
import ShortUniqueId from "npm:short-unique-id";

const generateOrderNo = () => `ORD-${new Date().toISOString().slice(2,10).replace(/-/g,"")}-${new ShortUniqueId({length:8}).rnd()}`;

async function createAppPrepay(MERCHANT_ID, MERCHANT_APP_ID, MCH_CERT_SERIAL_NO, MCH_PRIVATE_KEY, WECHAT_PAY_PUBLIC_KEY_ID, WECHAT_PAY_PUBLIC_KEY, outTradeNo, amount, notifyUrl, description) {
  try {
    const wxpay = new Wechatpay({
      mchid: MERCHANT_ID,
      serial: MCH_CERT_SERIAL_NO,
      privateKey: MCH_PRIVATE_KEY,
      certs: { [WECHAT_PAY_PUBLIC_KEY_ID]: WECHAT_PAY_PUBLIC_KEY },
    });

    const { data } = await wxpay.v3.pay.transactions.app.post({
      mchid: MERCHANT_ID,
      appid: MERCHANT_APP_ID,
      description: description || '商品购买',
      out_trade_no: outTradeNo,
      notify_url: notifyUrl,
      amount: { total: Math.round(amount * 100), currency: 'CNY' },
    }, { headers: { 'Wechatpay-Serial': WECHAT_PAY_PUBLIC_KEY_ID } });

    if (data.prepay_id) {
      // Secondary signature for client invocation
      const nonceStr = Formatter.nonce();
      const timeStamp = '' + Formatter.timestamp();
      const packageStr = 'Sign=WXPay';
      const signStr = Formatter.joinedByLineFeed(MERCHANT_APP_ID, timeStamp, nonceStr, data.prepay_id);
      const sign = Rsa.sign(signStr, Rsa.from(MCH_PRIVATE_KEY));

      return {
        success: true,
        paymentParams: {
          appId: MERCHANT_APP_ID,
          partnerId: MERCHANT_ID,
          prepayId: data.prepay_id,
          nonceStr,
          timeStamp,
          package: packageStr,
          sign,
        }
      };
    } else {
      return { success: false, error: "发起支付失败" };
    }
  } catch (err) {
    console.error(`[WeChatPay APP ERROR] outTradeNo=${outTradeNo}, error=${err?.message || String(err)}`);
    return { success: false, error: err?.message || String(err) };
  }
}

// app_payment_callback Edge Function
import { Aes } from "npm:wechatpay-axios-plugin@0.9.4";

async function decryptTradeState(MCH_API_V3_KEY: string, associatedData: string, nonce: string, ciphertext: string): Promise<{ tradeState: string; outTradeNo: string; transactionId: string }> {
  const plaintext = await Aes.AesGcm.decrypt(ciphertext, MCH_API_V3_KEY, nonce, associatedData);
  const obj = JSON.parse(plaintext);
  return {
    tradeState: (obj.trade_state ?? "") === "SUCCESS" ? "SUCCESS" : "OTHERS",
    outTradeNo: obj.out_trade_no ?? "",
    transactionId: obj.transaction_id ?? ""
  };
}
```

Recommended Items (Payment):
1. **Polling mechanism**: Implement polling every 2 seconds on order result page to check order status. If payment is successful, display success UI and navigate to next business flow.
2. For inventory management, encapsulate all data mutations in RPC functions as atomic transactions to maintain consistency.
3. Display detailed error messages on the frontend when SECRETS are misconfigured or WeChat Pay API calls fail.
4. Suggested order number format: `ORD-YYMMDD-XXXXXXXX` (8-char random suffix).
</PAYMENT_REQUIREMENTS>

<CLIENT_IMPLEMENTATION>
Required Items (Client — Expo + React Native):
1. **Dependencies**: `pnpm exec expo install expo-native-wechat`
   - `expo-linking`: Already included in boilerplate — no install needed
   - `expo-native-wechat`: WeChat OpenSDK wrapper for Expo (supports payment, auth, sharing)
2. **app.json configuration**:
   ```json
   {
     "expo": {
       "ios": {
         "associatedDomains": ["applinks:app-{appId}.appmiaoda.com"]
       },
       "plugins": [
         "expo-native-wechat"
       ]
     }
   }
   ```
   - iOS: `associatedDomains` for Universal Link (WeChat return after payment)
   - Android: ensure package name and signing config are correct
   - Plugin declaration is REQUIRED — `expo-native-wechat` needs native code linking
3. **SDK Registration** (must call before any WeChat API):
   ```typescript
   import { registerApp } from "expo-native-wechat";
   // Call once at app startup (e.g., in root _layout.tsx useEffect)
   useEffect(() => { registerApp(WECHAT_APP_ID); }, []);
   ```
   - `WECHAT_APP_ID` is the WeChat Open Platform AppID (same as MERCHANT_APP_ID used server-side)
   - This is a CLIENT-SIDE constant (AppID is public, NOT a secret)
4. **Payment flow**:
   - User taps pay button → POST to `create_app_payment` Edge Function with `{ product_id, quantity }`
   - Receive `paymentParams` from Edge Function
   - Invoke WeChat SDK:
     ```typescript
     import { requestPayment } from "expo-native-wechat";
     const result = await requestPayment({
       partnerId: paymentParams.partnerId,
       prepayId: paymentParams.prepayId,
       nonceStr: paymentParams.nonceStr,
       timeStamp: paymentParams.timeStamp,
       sign: paymentParams.sign,
     });
     ```
   - Note: `appId` and `package` are NOT passed to `requestPayment` — SDK handles them internally
   - After payment completes/cancels → navigate to result page
   - Result page polls `query_order_status` (2s interval, max 30s timeout)
   - On `status === 'paid'` → show success UI
   - **IMPORTANT**: `requestPayment` result does NOT guarantee payment status. MUST poll server to confirm.
5. **Universal Link / AASA**:
   - `associatedDomains` in app.json is auto-configured by platform (Sandbox) — Agent keeps the declaration in app.json as a fallback
   - AASA file content is assembled by the platform frontend and provided to Agent — Agent does NOT generate AASA content itself
   - Agent writes the provided AASA JSON to `public/.well-known/apple-app-site-association` if instructed
   - Domain: `app-{appId}.appmiaoda.com`
6. **PROHIBITED — violations will break the app**:
   - ❌ ANY secret key, private key, or APIv3 key in client code
   - ❌ Client directly calling WeChat Pay API
   - ❌ Client calculating or transmitting payment amount
   - ❌ Using URL Scheme for iOS return (MUST use Universal Link)
   - ❌ Using `expo-av` for any media (use `expo-video`)
</CLIENT_IMPLEMENTATION>

<REFUND_REQUIREMENTS>
Required Items (Refund — only implement if user explicitly requires refund):
1. Edge functions: `refund_order`, `app_refund_callback`
2. **refund_order**:
   - Validate refund amount ≤ paid amount
   - Generate refund_no
   - Call WeChat refund API: `wxpay.v3.refund.domestic.refunds.post(...)`
   - Update refund record status to 'processing'
3. **app_refund_callback** (TX3 — Atomic):
   - Decrypt refund notification
   - **SUCCESS**: Update refund status + update order refunded_amount + adjust inventory if needed
   - **CLOSED/ABNORMAL**: Update refund status, notify admin
4. Utility functions below must be used unmodified.

```typescript
// refund_order Edge Function
import Wechatpay from "npm:wechatpay-axios-plugin@0.9.4";
import ShortUniqueId from "npm:short-unique-id";

const generateRefundNo = () => `REF-${new Date().toISOString().slice(2,10).replace(/-/g,"")}-${new ShortUniqueId({length:8}).rnd()}`;

async function createWechatRefund(MERCHANT_ID, MCH_CERT_SERIAL_NO, MCH_PRIVATE_KEY, WECHAT_PAY_PUBLIC_KEY_ID, WECHAT_PAY_PUBLIC_KEY, outTradeNo, outRefundNo, refundAmount, totalAmount, reason, notifyUrl) {
  try {
    const wxpay = new Wechatpay({
      mchid: MERCHANT_ID,
      serial: MCH_CERT_SERIAL_NO,
      privateKey: MCH_PRIVATE_KEY,
      certs: { [WECHAT_PAY_PUBLIC_KEY_ID]: WECHAT_PAY_PUBLIC_KEY },
    });

    const { data } = await wxpay.v3.refund.domestic.refunds.post({
      out_trade_no: outTradeNo,
      out_refund_no: outRefundNo,
      reason: reason || "退款",
      notify_url: notifyUrl,
      amount: {
        refund: Math.round(refundAmount * 100),
        total: Math.round(totalAmount * 100),
        currency: "CNY"
      }
    }, { headers: { "Wechatpay-Serial": WECHAT_PAY_PUBLIC_KEY_ID } });

    if (data.refund_id) {
      return { success: true, refundId: data.refund_id, status: data.status };
    } else {
      return { success: false, error: "发起退款失败" };
    }
  } catch (err) {
    console.error(`[WeChatRefund ERROR] outRefundNo=${outRefundNo}, error=${err?.message || String(err)}`);
    return { success: false, error: err?.message || String(err) };
  }
}

// app_refund_callback Edge Function
import { Aes } from "npm:wechatpay-axios-plugin@0.9.4";

async function decryptRefundState(MCH_API_V3_KEY: string, associatedData: string, nonce: string, ciphertext: string): Promise<{ refundStatus: string; outTradeNo: string; outRefundNo: string }> {
  const plaintext = await Aes.AesGcm.decrypt(ciphertext, MCH_API_V3_KEY, nonce, associatedData);
  const obj = JSON.parse(plaintext);
  return {
    refundStatus: obj.refund_status ?? "",
    outTradeNo: obj.out_trade_no ?? "",
    outRefundNo: obj.out_refund_no ?? ""
  };
}
```
</REFUND_REQUIREMENTS>

<DB_SCHEMA>
Recommended database schema:
```sql
create type order_status as enum ('pending', 'paid', 'refunded', 'cancelled');

create table public.orders (
  id uuid primary key default gen_random_uuid(),
  order_no text unique not null,
  user_id uuid not null references auth.users(id),
  product_id text not null,
  quantity int not null default 1,
  amount numeric(12,2) not null,
  status order_status not null default 'pending',
  out_trade_no text unique not null,
  transaction_id text,
  refunded_amount numeric(12,2) default 0,
  version int default 0,
  paid_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- RLS: users can only read their own orders
alter table public.orders enable row level security;
create policy "Users can view own orders" on public.orders
  for select using (auth.uid() = user_id);

-- Order status updates only by service_role (Edge Functions)
-- No INSERT/UPDATE/DELETE policy for authenticated users on status changes
```
</DB_SCHEMA>
</APP_PAYMENT_REQUIREMENTS>
