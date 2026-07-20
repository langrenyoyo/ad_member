# App API 接入说明

Base URL: `/mas`

所有 App 接口返回统一结构：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

`code` 非 `0` 表示业务失败。所有 `/mas/app/*` 接口必须携带 App 签名请求头。

## App 签名安全规范

### 服务端配置

服务端从 `system_configs` 或环境变量读取 App 鉴权配置：

| 配置项 | 环境变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `app_api_auth_enabled` | `APP_API_AUTH_ENABLED` | `1` | `1` 启用签名校验，`0` 关闭 |
| `app_api_key` | `APP_API_KEY` | `ad_member_app` | App 调用方标识 |
| `app_api_secret` | `APP_API_SECRET` | 空 | HMAC 密钥，生产环境必须配置 |
| `app_api_time_window_seconds` | `APP_API_TIME_WINDOW_SECONDS` | `300` | 时间戳允许偏差秒数 |

生产环境必须配置 `app_api_secret` 或 `APP_API_SECRET`。不要把密钥放进接口返回值、日志或前端管理端代码。

### 请求头

每次调用 `/mas/app/*` 都需要带以下请求头：

| Header | 必填 | 示例 | 说明 |
| --- | --- | --- | --- |
| `X-App-Key` | 是 | `ad_member_app` | App Key |
| `X-App-Timestamp` | 是 | `1784553600` | Unix 秒级时间戳 |
| `X-App-Nonce` | 是 | `uuid-v4` | 随机串，同一时间窗内不可重复 |
| `X-App-Signature` | 是 | `hex-string` | HMAC-SHA256 十六进制签名 |

### 签名算法

App 端先计算请求体 SHA256：

```text
body_hash = SHA256(raw_request_body_bytes).hex()
```

GET 请求没有 body 时，使用空字节的 SHA256：

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

然后拼接 canonical string：

```text
METHOD
PATH
SORTED_QUERY
BODY_HASH
TIMESTAMP
NONCE
```

说明：

- `METHOD`: 大写 HTTP 方法，例如 `GET`、`POST`。
- `PATH`: 实际请求路径，包含 `/mas`，例如 `/mas/app/member/sync`。
- `SORTED_QUERY`: query 参数按 `key/value` 排序后 URL 编码，不带 `?`。没有 query 时为空行。
- `BODY_HASH`: 原始请求体字节的 SHA256 hex。POST JSON 签名时必须用实际发送的 JSON 字符串。
- `TIMESTAMP`: 与 `X-App-Timestamp` 完全一致。
- `NONCE`: 与 `X-App-Nonce` 完全一致。

最终签名：

```text
X-App-Signature = HMAC_SHA256_HEX(app_api_secret, canonical_string)
```

### 伪代码

```js
const body = JSON.stringify(payload)
const bodyHash = sha256Hex(body)
const canonical = [
  method.toUpperCase(),
  path,
  sortedQuery,
  bodyHash,
  timestamp,
  nonce,
].join('\n')
const signature = hmacSha256Hex(appSecret, canonical)
```

### 安全要求

- 时间戳超过允许窗口会返回 `app_timestamp_expired`。
- 同一 `X-App-Key + X-App-Nonce` 在时间窗内重复会返回 `app_nonce_replayed`。
- 签名错误返回 `app_signature_invalid`。
- 缺少签名头返回 `app_signature_headers_required`。
- 服务端当前使用进程内 nonce 缓存；多实例部署时应替换为 Redis 等共享存储。
- 广告平台回调接口不使用这套 App 签名，仍使用各平台自身签名规则。

## 获取 App 配置

`GET /app/config`

返回公开配置、Taku 应用列表和广告平台回调地址。接口不会返回 Taku Publisher Key 或各广告平台 security key。

## 同步会员和设备

`POST /app/member/sync`

App 登录或启动后调用，用于创建或更新会员基础资料，并绑定当前设备。

```json
{
  "uid": "U10001",
  "nickname": "Tom",
  "mobile": "13800000000",
  "device_model": "iPhone 15",
  "device_unique_id": "idfa-or-oaid",
  "platform": 2
}
```

## 绑定设备

`POST /app/device/bind`

```json
{
  "uid": "U10001",
  "device_model": "Pixel 8",
  "device_unique_id": "oaid-value",
  "platform": 1
}
```

`platform`: `0` unknown, `1` Android, `2` iOS.

## 获取会员资料

`GET /app/member/profile?uid=U10001`

返回会员状态、收益余额、最近设备记录。App 可用 `status` 和 `is_black` 判断账号是否可继续参与广告激励。

## 风控预检

`POST /app/risk/precheck`

展示激励广告前调用，用于检查账号、设备、IP、频次等风控规则。

```json
{
  "uid": "U10001",
  "trans_id": "tx_20260720_001",
  "device_id": "oaid-value",
  "device_model": "Pixel 8",
  "device_unique_id": "oaid-value",
  "platform": 1
}
```

返回：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "passed": true,
    "risk_score": 0,
    "hits": []
  }
}
```

## 上报广告事件

`POST /app/ad/event`

用于记录 App 端广告展示、点击、关闭等事件，并同步设备与风控日志。

```json
{
  "uid": "U10001",
  "app_id": "taku-app-id",
  "app_name": "Demo App",
  "placement": "reward_video_home",
  "action": "show",
  "revenue": 0,
  "trans_id": "tx_20260720_001",
  "device_id": "oaid-value",
  "device_model": "Pixel 8",
  "device_unique_id": "oaid-value",
  "platform": 1
}
```

注意：该接口只记录 App 事件，不直接发放奖励。真实奖励仍由广告平台回调和 Taku S2S 回调共同确认。

## 查询奖励状态

`GET /app/reward/status?trans_id=tx_20260720_001&uid=U10001`

返回单笔激励事务状态：

- `pending`: 已收到主回调，等待另一侧验证或延迟确认。
- `confirmed`: 平台回调和 Taku S2S 均通过，奖励已确认。
- `rejected`: 风控或签名失败。
- `clawback`: 对账核减。

## 查询会员奖励流水

`GET /app/member/transactions?uid=U10001&page=1&limit=20&status=confirmed`

`status` 可为空，或传 `pending`、`confirmed`、`rejected`、`clawback`。

## 广告回调地址

广告平台服务端回调仍使用已有地址：

- 快手: `/mas/callback/kuaishou/reward`
- 腾讯优量汇: `/mas/callback/tencent/reward`
- 百度广告: `/mas/callback/baidu/reward`
- Taku S2S: `/mas/callback/taku/s2s`
