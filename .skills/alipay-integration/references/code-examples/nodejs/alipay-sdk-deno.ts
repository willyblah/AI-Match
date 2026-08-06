/**
 * alipay-sdk-deno — 单文件版
 * Deno / Supabase Edge Function 兼容，零外部依赖
 * 基于 alipay-sdk@4.14.0 改造，使用 WebCrypto + fetch 替代 urllib/node:crypto/node:stream
 */

// ══════════════════════════════════════════════════════════════════════════════
// types
// ══════════════════════════════════════════════════════════════════════════════

export type AlipaySdkSignType = 'RSA2' | 'RSA';

export interface AlipaySdkConfig {
  appId: string;
  privateKey: string;
  signType?: AlipaySdkSignType;
  alipayPublicKey?: string;
  gateway?: string;
  endpoint?: string;
  timeout?: number;
  camelcase?: boolean;
  charset?: 'utf-8';
  version?: '1.0';
  keyType?: 'PKCS1' | 'PKCS8';
  appCertContent?: string;
  appCertSn?: string;
  alipayRootCertContent?: string;
  alipayRootCertSn?: string;
  alipayPublicCertContent?: string;
  alipayCertSn?: string;
  encryptKey?: string;
  wsServiceUrl?: string;
}

type PrivateKeyType = 'PKCS1' | 'PKCS8';

interface Asn1Tlv {
  tag: number;
  valueOffset: number;
  nextOffset: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// 二进制 / Base64 工具
// ══════════════════════════════════════════════════════════════════════════════

function base64ToUint8Array(b64: string): Uint8Array {
  const binary = atob(b64.replace(/\s/g, ''));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function uint8ArrayToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function pemToBase64(pem: string): string {
  return pem.split('\n').filter(l => !l.startsWith('-----')).join('').replace(/\s/g, '');
}

function pemToBytes(pem: string): Uint8Array {
  return base64ToUint8Array(pemToBase64(pem));
}

function readAsn1Tlv(bytes: Uint8Array, offset: number): Asn1Tlv {
  if (offset + 2 > bytes.length) throw new Error('invalid private key DER');

  const tag = bytes[offset++];
  const firstLengthByte = bytes[offset++];
  let length = 0;

  if (firstLengthByte < 0x80) {
    length = firstLengthByte;
  } else {
    const lengthByteCount = firstLengthByte & 0x7f;
    if (lengthByteCount === 0 || lengthByteCount > 4 || offset + lengthByteCount > bytes.length) {
      throw new Error('invalid private key DER');
    }
    for (let i = 0; i < lengthByteCount; i++) length = (length << 8) | bytes[offset++];
  }

  const valueOffset = offset;
  const nextOffset = valueOffset + length;
  if (nextOffset > bytes.length) throw new Error('invalid private key DER');
  return { tag, valueOffset, nextOffset };
}

function detectPrivateKeyType(privateKey: string): PrivateKeyType {
  const normalizedKey = privateKey.trim();
  let declaredKeyType: PrivateKeyType | undefined;
  if (normalizedKey.includes('-----BEGIN RSA PRIVATE KEY-----')) declaredKeyType = 'PKCS1';
  else if (normalizedKey.includes('-----BEGIN PRIVATE KEY-----')) declaredKeyType = 'PKCS8';
  else if (normalizedKey.includes('-----BEGIN')) throw new Error('unsupported private key PEM format');

  const der = pemToBytes(normalizedKey);
  const outer = readAsn1Tlv(der, 0);
  if (outer.tag !== 0x30 || outer.nextOffset !== der.length) throw new Error('invalid private key DER');

  const version = readAsn1Tlv(der, outer.valueOffset);
  if (version.tag !== 0x02) throw new Error('invalid private key DER');
  const secondField = readAsn1Tlv(der, version.nextOffset);
  const detectedKeyType = secondField.tag === 0x02 ? 'PKCS1'
    : secondField.tag === 0x30 ? 'PKCS8'
    : undefined;
  if (!detectedKeyType) throw new Error('unsupported private key DER format');
  if (declaredKeyType && declaredKeyType !== detectedKeyType) {
    throw new Error('private key PEM header does not match its DER format');
  }
  return detectedKeyType;
}

function uint8ArrayToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

function concatUint8Arrays(...arrays: Uint8Array[]): Uint8Array {
  const total = arrays.reduce((s, a) => s + a.length, 0);
  const result = new Uint8Array(total);
  let offset = 0;
  for (const arr of arrays) { result.set(arr, offset); offset += arr.length; }
  return result;
}

// ══════════════════════════════════════════════════════════════════════════════
// ASN.1 / DER 最小解析器
// ══════════════════════════════════════════════════════════════════════════════

interface Asn1Node { tag: number; length: number; value: Uint8Array; end: number }

function parseSequenceChildren(buf: Uint8Array): Asn1Node[] {
  const result: Asn1Node[] = [];
  let pos = 0;
  while (pos < buf.length) {
    const tag = buf[pos];
    if (tag === 0) break;
    const lenByte = buf[pos + 1];
    let length: number, headerLen: number;
    if (lenByte < 0x80) { length = lenByte; headerLen = 2; }
    else {
      const n = lenByte & 0x7f;
      length = 0;
      for (let i = 0; i < n; i++) length = (length << 8) | buf[pos + 2 + i];
      headerLen = 2 + n;
    }
    result.push({ tag, length, value: buf.slice(pos + headerLen, pos + headerLen + length), end: pos + headerLen + length });
    pos += headerLen + length;
  }
  return result;
}

function decodeOID(bytes: Uint8Array): string {
  const parts: number[] = [Math.floor(bytes[0] / 40), bytes[0] % 40];
  let value = 0;
  for (let i = 1; i < bytes.length; i++) {
    value = (value << 7) | (bytes[i] & 0x7f);
    if ((bytes[i] & 0x80) === 0) { parts.push(value); value = 0; }
  }
  return parts.join('.');
}

const OID_SHORT_NAME: Record<string, string> = {
  '2.5.4.3': 'CN', '2.5.4.6': 'C', '2.5.4.7': 'L', '2.5.4.8': 'ST',
  '2.5.4.10': 'O', '2.5.4.11': 'OU', '2.5.4.5': 'serialNumber',
};

function decodeRDNSequence(bytes: Uint8Array): Array<{ shortName: string; value: string }> {
  const result: Array<{ shortName: string; value: string }> = [];
  for (const rdn of parseSequenceChildren(bytes)) {
    for (const attrSeq of parseSequenceChildren(rdn.value)) {
      const attrs = parseSequenceChildren(attrSeq.value);
      if (attrs.length < 2) continue;
      const oid = decodeOID(attrs[0].value);
      result.push({ shortName: OID_SHORT_NAME[oid] ?? oid, value: new TextDecoder().decode(attrs[1].value) });
    }
  }
  return result;
}

function extractCertFields(der: Uint8Array): { issuerBytes: Uint8Array; serialNumber: string; signatureOID: string } {
  const certNode = parseSequenceChildren(der)[0]; // 整个 Certificate SEQUENCE
  // 重新解析顶层
  const top = parseSequenceChildren(der);           // Certificate children: tbs, sigAlg, sig
  const sigAlgChildren = parseSequenceChildren(top[1].value);
  const signatureOID = decodeOID(sigAlgChildren[0].value);
  const tbsChildren = parseSequenceChildren(top[0].value);
  let idx = tbsChildren[0].tag === 0xa0 ? 1 : 0;
  const serialNumber = uint8ArrayToHex(tbsChildren[idx].value);
  const issuerBytes = tbsChildren[idx + 2].value;
  return { issuerBytes, serialNumber, signatureOID };
}

// ══════════════════════════════════════════════════════════════════════════════
// MD5（纯 JS，用于证书 SN 计算，SubtleCrypto 不支持 MD5）
// ══════════════════════════════════════════════════════════════════════════════

function md5(input: string): string {
  function safeAdd(x: number, y: number) { const l = (x & 0xffff) + (y & 0xffff); return ((x >> 16) + (y >> 16) + (l >> 16)) << 16 | (l & 0xffff); }
  function rol(n: number, c: number) { return n << c | n >>> (32 - c); }
  function cmn(q: number, a: number, b: number, x: number, s: number, t: number) { return safeAdd(rol(safeAdd(safeAdd(a, q), safeAdd(x, t)), s), b); }
  const ff = (a: number, b: number, c: number, d: number, x: number, s: number, t: number) => cmn(b & c | ~b & d, a, b, x, s, t);
  const gg = (a: number, b: number, c: number, d: number, x: number, s: number, t: number) => cmn(b & d | c & ~d, a, b, x, s, t);
  const hh = (a: number, b: number, c: number, d: number, x: number, s: number, t: number) => cmn(b ^ c ^ d, a, b, x, s, t);
  const ii = (a: number, b: number, c: number, d: number, x: number, s: number, t: number) => cmn(c ^ (b | ~d), a, b, x, s, t);

  const utf8 = new TextEncoder().encode(input);
  const msgLen = utf8.length;
  const paddedLen = msgLen + 64 - (msgLen + 8) % 64 + 8;
  const padded = new Uint8Array(paddedLen + 8);
  padded.set(utf8); padded[msgLen] = 0x80;
  const bitLen = msgLen * 8;
  padded[paddedLen] = bitLen & 0xff; padded[paddedLen + 1] = (bitLen >> 8) & 0xff;
  padded[paddedLen + 2] = (bitLen >> 16) & 0xff; padded[paddedLen + 3] = (bitLen >> 24) & 0xff;
  const m = new Int32Array(padded.buffer);
  let a = 1732584193, b = -271733879, c = -1732584194, d = 271733878;
  for (let i = 0; i < m.length; i += 16) {
    const [aa, bb, cc, dd] = [a, b, c, d];
    a=ff(a,b,c,d,m[i],7,-680876936);d=ff(d,a,b,c,m[i+1],12,-389564586);c=ff(c,d,a,b,m[i+2],17,606105819);b=ff(b,c,d,a,m[i+3],22,-1044525330);
    a=ff(a,b,c,d,m[i+4],7,-176418897);d=ff(d,a,b,c,m[i+5],12,1200080426);c=ff(c,d,a,b,m[i+6],17,-1473231341);b=ff(b,c,d,a,m[i+7],22,-45705983);
    a=ff(a,b,c,d,m[i+8],7,1770035416);d=ff(d,a,b,c,m[i+9],12,-1958414417);c=ff(c,d,a,b,m[i+10],17,-42063);b=ff(b,c,d,a,m[i+11],22,-1990404162);
    a=ff(a,b,c,d,m[i+12],7,1804603682);d=ff(d,a,b,c,m[i+13],12,-40341101);c=ff(c,d,a,b,m[i+14],17,-1502002290);b=ff(b,c,d,a,m[i+15],22,1236535329);
    a=gg(a,b,c,d,m[i+1],5,-165796510);d=gg(d,a,b,c,m[i+6],9,-1069501632);c=gg(c,d,a,b,m[i+11],14,643717713);b=gg(b,c,d,a,m[i],20,-373897302);
    a=gg(a,b,c,d,m[i+5],5,-701558691);d=gg(d,a,b,c,m[i+10],9,38016083);c=gg(c,d,a,b,m[i+15],14,-660478335);b=gg(b,c,d,a,m[i+4],20,-405537848);
    a=gg(a,b,c,d,m[i+9],5,568446438);d=gg(d,a,b,c,m[i+14],9,-1019803690);c=gg(c,d,a,b,m[i+3],14,-187363961);b=gg(b,c,d,a,m[i+8],20,1163531501);
    a=gg(a,b,c,d,m[i+13],5,-1444681467);d=gg(d,a,b,c,m[i+2],9,-51403784);c=gg(c,d,a,b,m[i+7],14,1735328473);b=gg(b,c,d,a,m[i+12],20,-1926607734);
    a=hh(a,b,c,d,m[i+5],4,-378558);d=hh(d,a,b,c,m[i+8],11,-2022574463);c=hh(c,d,a,b,m[i+11],16,1839030562);b=hh(b,c,d,a,m[i+14],23,-35309556);
    a=hh(a,b,c,d,m[i+1],4,-1530992060);d=hh(d,a,b,c,m[i+4],11,1272893353);c=hh(c,d,a,b,m[i+7],16,-155497632);b=hh(b,c,d,a,m[i+10],23,-1094730640);
    a=hh(a,b,c,d,m[i+13],4,681279174);d=hh(d,a,b,c,m[i],11,-358537222);c=hh(c,d,a,b,m[i+3],16,-722521979);b=hh(b,c,d,a,m[i+6],23,76029189);
    a=hh(a,b,c,d,m[i+9],4,-640364487);d=hh(d,a,b,c,m[i+12],11,-421815835);c=hh(c,d,a,b,m[i+15],16,530742520);b=hh(b,c,d,a,m[i+2],23,-995338651);
    a=ii(a,b,c,d,m[i],6,-198630844);d=ii(d,a,b,c,m[i+7],10,1126891415);c=ii(c,d,a,b,m[i+14],15,-1416354905);b=ii(b,c,d,a,m[i+5],21,-57434055);
    a=ii(a,b,c,d,m[i+12],6,1700485571);d=ii(d,a,b,c,m[i+3],10,-1894986606);c=ii(c,d,a,b,m[i+10],15,-1051523);b=ii(b,c,d,a,m[i+1],21,-2054922799);
    a=ii(a,b,c,d,m[i+8],6,1873313359);d=ii(d,a,b,c,m[i+15],10,-30611744);c=ii(c,d,a,b,m[i+6],15,-1560198380);b=ii(b,c,d,a,m[i+13],21,1309151649);
    a=ii(a,b,c,d,m[i+4],6,-145523070);d=ii(d,a,b,c,m[i+11],10,-1120210379);c=ii(c,d,a,b,m[i+2],15,718787259);b=ii(b,c,d,a,m[i+9],21,-343485551);
    a=safeAdd(a,aa);b=safeAdd(b,bb);c=safeAdd(c,cc);d=safeAdd(d,dd);
  }
  return [a,b,c,d].map(n => (n>>>0).toString(16).padStart(8,'0').match(/.{2}/g)!.reverse().join('')).join('');
}

// ══════════════════════════════════════════════════════════════════════════════
// antcertutil — 证书工具（无 node:fs，纯字符串输入）
// ══════════════════════════════════════════════════════════════════════════════

function computeCertSN(der: Uint8Array): string {
  const { issuerBytes, serialNumber } = extractCertFields(der);
  const attrs = decodeRDNSequence(issuerBytes);
  const principalName = attrs.reduceRight((prev, curr) => `${prev}${curr.shortName}=${curr.value},`, '').slice(0, -1);
  const decimalNumber = BigInt('0x' + serialNumber).toString(10);
  return md5(principalName + decimalNumber);
}

export function getSN(pem: string, isRoot = false): string {
  if (!isRoot) return computeCertSN(pemToBytes(pem));
  const blocks = pem.match(/-----BEGIN CERTIFICATE-----[\s\S]+?-----END CERTIFICATE-----/g) ?? [];
  let sn = '';
  for (const block of blocks) {
    const { signatureOID } = extractCertFields(pemToBytes(block));
    if (signatureOID.startsWith('1.2.840.113549.1.1')) {
      const s = computeCertSN(pemToBytes(block));
      sn = sn ? `${sn}_${s}` : s;
    }
  }
  return sn;
}

export function loadPublicKey(pem: string): string {
  const der = pemToBytes(pem);
  const top = parseSequenceChildren(der);
  const tbsChildren = parseSequenceChildren(top[0].value);
  let idx = tbsChildren[0].tag === 0xa0 ? 1 : 0;
  const spkiChildren = parseSequenceChildren(tbsChildren[idx + 5].value);
  return uint8ArrayToBase64(spkiChildren[1].value.slice(1)); // 去掉 BIT STRING 首字节
}

// ══════════════════════════════════════════════════════════════════════════════
// util — 签名、加密、格式转换
// ══════════════════════════════════════════════════════════════════════════════

export const ALIPAY_ALGORITHM_MAPPING: Record<string, string> = { RSA: 'RSA-SHA1', RSA2: 'RSA-SHA256' };

/** 格式化为 yyyy-MM-dd HH:mm:ss */
export function YYYYMMDDHHmmss(date: Date = new Date()): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${p(date.getMonth()+1)}-${p(date.getDate())} ${p(date.getHours())}:${p(date.getMinutes())}:${p(date.getSeconds())}`;
}

export function createRequestId(): string { return crypto.randomUUID().replaceAll('-', ''); }

// ── PKCS#1 → PKCS#8 包装 ────────────────────────────────────────────────────

function encodeAsn1TLV(tag: number, value: Uint8Array): Uint8Array {
  const len = value.length;
  const lenBytes = len < 0x80 ? new Uint8Array([len])
    : len < 0x100 ? new Uint8Array([0x81, len])
    : new Uint8Array([0x82, (len >> 8) & 0xff, len & 0xff]);
  return concatUint8Arrays(new Uint8Array([tag]), lenBytes, value);
}

function wrapPkcs1InPkcs8(pkcs1Der: Uint8Array): Uint8Array {
  const algId = new Uint8Array([0x30,0x0d,0x06,0x09,0x2a,0x86,0x48,0x86,0xf7,0x0d,0x01,0x01,0x01,0x05,0x00]);
  const version = new Uint8Array([0x02,0x01,0x00]);
  return encodeAsn1TLV(0x30, concatUint8Arrays(version, algId, encodeAsn1TLV(0x04, pkcs1Der)));
}

async function importPrivateKey(pem: string): Promise<CryptoKey> {
  const isPkcs8 = pem.includes('PRIVATE KEY') && !pem.includes('RSA PRIVATE KEY');
  const der = isPkcs8 ? base64ToUint8Array(pemToBase64(pem)) : wrapPkcs1InPkcs8(base64ToUint8Array(pemToBase64(pem)));
  return crypto.subtle.importKey('pkcs8', der.buffer, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
}

export async function signWithRSA(signString: string, privateKeyPem: string): Promise<string> {
  const key = await importPrivateKey(privateKeyPem);
  const sig = await crypto.subtle.sign({ name: 'RSASSA-PKCS1-v1_5' }, key, new TextEncoder().encode(signString));
  return uint8ArrayToBase64(new Uint8Array(sig));
}

export async function verifySignatureV3(signString: string, expectedSig: string, publicKeyPem: string): Promise<boolean> {
  const key = await crypto.subtle.importKey('spki', base64ToUint8Array(pemToBase64(publicKeyPem)).buffer, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  return crypto.subtle.verify({ name: 'RSASSA-PKCS1-v1_5' }, key, base64ToUint8Array(expectedSig), new TextEncoder().encode(signString));
}

// ── AES-CBC（替代 crypto-js，IV 全 0 与原 SDK 一致）──────────────────────────

const AES_IV = new Uint8Array(16);

async function importAesKey(base64Key: string): Promise<CryptoKey> {
  return crypto.subtle.importKey('raw', base64ToUint8Array(base64Key), 'AES-CBC', false, ['encrypt','decrypt']);
}

export async function aesEncryptText(plain: string, key: string): Promise<string> {
  const enc = await crypto.subtle.encrypt({ name:'AES-CBC', iv:AES_IV }, await importAesKey(key), new TextEncoder().encode(plain));
  return uint8ArrayToBase64(new Uint8Array(enc));
}

export async function aesDecryptText(encrypted: string, key: string): Promise<string> {
  const dec = await crypto.subtle.decrypt({ name:'AES-CBC', iv:AES_IV }, await importAesKey(key), base64ToUint8Array(encrypted));
  return new TextDecoder().decode(dec);
}

export async function aesEncrypt(data: object, key: string): Promise<string> { return aesEncryptText(JSON.stringify(data), key); }
export async function aesDecrypt(enc: string, key: string): Promise<object> { return JSON.parse(await aesDecryptText(enc, key)); }

// ── snakeCase / camelCase（内联，替代 snakecase-keys / camelcase-keys）────────

export function snakeCaseKeys(obj: Record<string,any>): Record<string,any> {
  if (Array.isArray(obj)) return obj.map(snakeCaseKeys) as any;
  if (typeof obj !== 'object' || obj === null) return obj;
  const toSnake = (s: string) => s.replace(/([\p{Lowercase_Letter}\d])(\p{Uppercase_Letter})/gu,'$1_$2').replace(/(\p{Uppercase_Letter}+)(\p{Uppercase_Letter}\p{Lowercase_Letter}+)/gu,'$1_$2').toLowerCase();
  return Object.fromEntries(Object.entries(obj).map(([k,v]) => [toSnake(k), typeof v==='object'&&v!==null ? snakeCaseKeys(v) : v]));
}

export function camelcaseKeys(obj: Record<string,any>): Record<string,any> {
  if (Array.isArray(obj)) return obj.map(camelcaseKeys) as any;
  if (typeof obj !== 'object' || obj === null) return obj;
  return Object.fromEntries(Object.entries(obj).map(([k,v]) => [k.replace(/_([a-z])/g,(_,c)=>c.toUpperCase()), typeof v==='object'&&v!==null ? camelcaseKeys(v) : v]));
}

export function decamelize(text: string): string {
  if (typeof text !== 'string') throw new TypeError('`text` must be a string');
  return text.replace(/([\p{Lowercase_Letter}\d])(\p{Uppercase_Letter})/gu,'$1_$2').replace(/(\p{Uppercase_Letter})(\p{Uppercase_Letter}\p{Lowercase_Letter}+)/gu,'$1_$2').toLowerCase();
}

// ── OpenAPI 2.0 sign（异步）────────────────────────────────────────────────

export async function sign(
  method: string,
  params: Record<string,any>,
  config: Required<AlipaySdkConfig>,
  opts?: { bizContentAutoSnakeCase?: boolean },
): Promise<Record<string,any>> {
  const sp: Record<string,any> = { method, appId: config.appId, charset: config.charset, version: config.version, signType: config.signType, timestamp: YYYYMMDDHHmmss() };
  for (const k in params) { if (!['bizContent','biz_content','needEncrypt'].includes(k)) sp[k] = params[k]; }
  if (config.appCertSn && config.alipayRootCertSn) { sp.appCertSn = config.appCertSn; sp.alipayRootCertSn = config.alipayRootCertSn; }
  if (config.wsServiceUrl) sp.wsServiceUrl = config.wsServiceUrl;
  if (params.bizContent && params.biz_content) throw new TypeError('不能同时设置 bizContent 和 biz_content');
  let bizContent = params.bizContent ?? params.biz_content;
  if (bizContent) {
    if (opts?.bizContentAutoSnakeCase !== false) bizContent = snakeCaseKeys(bizContent);
    sp.bizContent = params.needEncrypt ? await aesEncrypt(bizContent, config.encryptKey!) : JSON.stringify(bizContent);
    if (params.needEncrypt) sp.encryptType = 'AES';
  }
  const dp = snakeCaseKeys(sp);
  const signString = Object.keys(dp).sort().map(k => `${k}=${typeof dp[k]==='string'?dp[k]:JSON.stringify(dp[k])}`).join('&');
  dp.sign = await signWithRSA(signString, config.privateKey);
  return dp;
}

// ══════════════════════════════════════════════════════════════════════════════
// form
// ══════════════════════════════════════════════════════════════════════════════

export interface IField { name: string; value: string | object }

export class AlipayFormData {
  public fields: IField[] = [];
  private method = 'post';
  getFields() { return this.fields; }
  getMethod() { return this.method; }
  setMethod(m: string) { this.method = m.toLowerCase(); }
  addField(name: string, value: any) {
    this.fields.push({ name, value: _isJSON(value) ? JSON.parse(value) : value });
  }
}

function _isJSON(v: any): boolean {
  if (typeof v !== 'string') return false;
  const t = v.replace(/\s|\n|\r/g,'');
  if (/^\{.*\}$/.test(t)) return /".*":.*/.test(t);
  return false;
}

// ══════════════════════════════════════════════════════════════════════════════
// 错误类型
// ══════════════════════════════════════════════════════════════════════════════

export interface AlipayRequestErrorOptions extends ErrorOptions {
  code?: string; traceId?: string; responseHttpStatus?: number; responseDataRaw?: string;
}

export class AlipayRequestError extends Error {
  code?: string; traceId?: string; responseHttpStatus?: number; responseDataRaw?: string;
  constructor(message: string, options?: AlipayRequestErrorOptions) {
    if (options?.traceId) message = `${message} (traceId: ${options.traceId})`;
    super(message, options);
    Object.assign(this, options);
    this.name = 'AlipayRequestError';
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// AlipaySdk 主类
// ══════════════════════════════════════════════════════════════════════════════

export interface AlipaySdkCommonResult { code: string; msg: string; sub_code?: string; sub_msg?: string; traceId?: string; [k: string]: any }
export type IPageExecuteMethod = 'GET' | 'POST';
export interface IRequestParams { [k: string]: any; bizContent?: Record<string,any>; needEncrypt?: boolean }
export interface IRequestOption { validateSign?: boolean; log?: { info(...a: any[]): any; error(...a: any[]): any }; traceId?: string }
export interface ISdkExecuteOptions { bizContentAutoSnakeCase?: boolean }

/**
 * Alipay OpenAPI SDK — Deno / Supabase Edge Function 版
 *
 * 支持：
 *   - pageExec()：网站支付，返回自动提交的 HTML 表单字符串
 *   - exec()：OpenAPI 2.0 通用调用（查单、退款等）
 */
export class AlipaySdk {
  public readonly version = 'alipay-sdk-deno-1.0.0';
  public config: Required<AlipaySdkConfig>;

  constructor(config: AlipaySdkConfig) {
    if (!config.appId) throw new Error('config.appId is required');
    if (!config.privateKey) throw new Error('config.privateKey is required');

    const keyType = detectPrivateKeyType(config.privateKey);
    const isSandbox = keyType === 'PKCS1';
    const gateway = isSandbox
      ? 'https://openapi-sandbox.dl.alipaydev.com/gateway.do'
      : 'https://openapi.alipay.com/gateway.do';
    const endpoint = isSandbox
      ? 'https://openapi-sandbox.dl.alipaydev.com'
      : 'https://openapi.alipay.com';

    if (config.gateway && config.gateway !== gateway) {
      throw new Error(`${keyType} private key conflicts with gateway: ${config.gateway}`);
    }
    if (config.endpoint && config.endpoint !== endpoint) {
      throw new Error(`${keyType} private key conflicts with endpoint: ${config.endpoint}`);
    }

    config.keyType = keyType;
    config.gateway = gateway;
    config.endpoint = endpoint;
    const pemType = keyType === 'PKCS8' ? 'PRIVATE KEY' : 'RSA PRIVATE KEY';
    config.privateKey = this._fmtKey(config.privateKey, pemType);

    // 证书模式
    if (config.appCertContent) {
      config.appCertSn = getSN(config.appCertContent, false);
      config.alipayCertSn = config.alipayPublicCertContent ? getSN(config.alipayPublicCertContent, false) : '';
      config.alipayRootCertSn = config.alipayRootCertContent ? getSN(config.alipayRootCertContent, true) : '';
      if (config.alipayPublicCertContent) config.alipayPublicKey = this._fmtKey(loadPublicKey(config.alipayPublicCertContent), 'PUBLIC KEY');
    } else if (config.alipayPublicKey) {
      config.alipayPublicKey = this._fmtKey(config.alipayPublicKey, 'PUBLIC KEY');
    }

    this.config = Object.assign({
      gateway: 'https://openapi.alipay.com/gateway.do',
      endpoint: 'https://openapi.alipay.com',
      timeout: 5000, camelcase: true, signType: 'RSA2' as AlipaySdkSignType,
      charset: 'utf-8' as const, version: '1.0' as const, keyType: 'PKCS1' as const,
      alipayPublicKey: '', appCertContent: '', appCertSn: '',
      alipayRootCertContent: '', alipayRootCertSn: '',
      alipayPublicCertContent: '', alipayCertSn: '', encryptKey: '', wsServiceUrl: '',
    }, config) as Required<AlipaySdkConfig>;
  }

  private _fmtKey(key: string, type: string): string {
    const items = key.split('\n').map(v => v.trim());
    if (items[0].includes(type)) items.shift();
    if (items[items.length-1].includes(type)) items.pop();
    return `-----BEGIN ${type}-----\n${items.join('')}\n-----END ${type}-----`;
  }

  private _fmtUrl(url: string, params: Record<string,string>): { execParams: Record<string,string>; url: string } {
    const urlArgs = ['app_id','method','format','charset','sign_type','sign','timestamp','version','notify_url','return_url','auth_token','app_auth_token','app_cert_sn','alipay_root_cert_sn','ws_service_url'];
    const reqUrl = new URL(url);
    const execParams: Record<string,string> = {};
    for (const k in params) {
      if (urlArgs.includes(k)) reqUrl.searchParams.set(k, params[k]);
      else execParams[k] = params[k];
    }
    return { execParams, url: reqUrl.toString() };
  }

  private _escapeHtml(s: string): string {
    return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  /**
   * 生成网站支付 HTML 表单（alipay.trade.page.pay）
   * 返回值直接渲染到页面并 form.submit() 即可跳转支付宝收银台
   */
  public async pageExec(method: string, httpMethod: IPageExecuteMethod = 'POST', params: IRequestParams = {}): Promise<string> {
    const signed = await sign(method, params, this.config);
    const { execParams, url } = this._fmtUrl(this.config.gateway, signed);
    if (httpMethod === 'GET') {
      const qs = Object.keys(execParams).map(k => `${encodeURIComponent(k)}=${encodeURIComponent(execParams[k])}`).join('&');
      return qs ? `${url}&${qs}` : url;
    }
    const inputs = Object.keys(execParams).map(k => `<input type="hidden" name="${k}" value="${this._escapeHtml(execParams[k])}">`).join('\n');
    return `<form name="punchout_form" method="post" action="${url}">\n${inputs}\n<input type="submit" value="立即支付" style="display:none" >\n</form>\n<script>document.forms[0].submit();</script>`;
  }

  /**
   * 调用 OpenAPI 2.0 接口（查单、退款等），使用原生 fetch 替代 urllib
   */
  public async exec(method: string, params: IRequestParams = {}, options: IRequestOption & ISdkExecuteOptions = {}): Promise<AlipaySdkCommonResult> {
    const signed = await sign(method, params, this.config, { bizContentAutoSnakeCase: options.bizContentAutoSnakeCase });
    const { execParams, url } = this._fmtUrl(this.config.gateway, signed);
    const body = new URLSearchParams(execParams).toString();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), this.config.timeout);
    let resp: Response;
    try {
      resp = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body, signal: ctrl.signal });
    } catch (e: any) {
      throw new AlipayRequestError(`fetch 请求失败: ${e.message}`, { cause: e });
    } finally { clearTimeout(timer); }
    const text = await resp.text();
    if (!resp.ok) throw new AlipayRequestError(`HTTP ${resp.status}`, { responseHttpStatus: resp.status, responseDataRaw: text });
    let data: Record<string,any>;
    try { data = JSON.parse(text); } catch { throw new AlipayRequestError(`响应解析失败: ${text}`, { responseDataRaw: text }); }
    const key = Object.keys(data).find(k => k.endsWith('_response'));
    const result = key ? data[key] : data;
    return (this.config.camelcase ? camelcaseKeys(result) : result) as AlipaySdkCommonResult;
  }
}
