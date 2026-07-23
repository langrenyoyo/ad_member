# App API 接入文档

## 1. 基本约定

- Base URL：`/mas`
- App API 前缀：`/mas/app`
- 请求格式：`application/json`
- `platform`：`0` 未知，`1` Android，`2` iOS
- 时间格式：ISO 8601

统一成功响应：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

`code` 非 `0` 表示业务失败。

## 2. 请求签名

所有 `/mas/app/*` 请求默认必须携带：

| Header | 必填 | 说明 |
| --- | --- | --- |
| `X-App-Key` | 是 | App API 调用方标识，不是 TAKU App Key |
| `X-App-Timestamp` | 是 | Unix 秒级时间戳 |
| `X-App-Nonce` | 是 | 每次请求唯一随机字符串 |
| `X-App-Signature` | 是 | HMAC-SHA256 十六进制签名 |

签名原文：

```text
METHOD
PATH
SORTED_QUERY
BODY_SHA256
TIMESTAMP
NONCE
```

计算方式：

```text
signature = HMAC_SHA256_HEX(app_api_secret, canonical_string)
```

- `METHOD` 使用大写。
- `PATH` 包含 `/mas`，例如 `/mas/app/config`。
- Query 参数按 key/value 排序后进行 URL 编码，不包含 `?`。
- GET 空请求体的 SHA256 为 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- POST 必须对实际发送的原始 JSON 字节计算 SHA256。
- 默认时间窗口为 300 秒；Nonce 在窗口内不可重复。

## 3. 用户信息接口

### 3.1 同步用户

`POST /mas/app/member/sync`

用于 App 登录或启动后创建、更新用户，并可同时绑定设备。

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

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `uid` | 是 | App 用户唯一 ID |
| `nickname` | 否 | 昵称 |
| `mobile` | 否 | 手机号 |
| `device_model` | 否 | 设备型号 |
| `device_unique_id` | 否 | IDFA、OAID 等设备唯一标识 |
| `platform` | 否 | 客户端平台 |

返回 `member`、`device` 和公开风控配置。

### 3.2 绑定设备

`POST /mas/app/device/bind`

```json
{
  "uid": "U10001",
  "device_model": "iPhone 15",
  "device_unique_id": "idfa-value",
  "platform": 2
}
```

`device_model` 和 `device_unique_id` 至少提供一项。

### 3.3 获取用户资料

`GET /mas/app/member/profile?uid=U10001`

返回用户状态、黑名单标记、收益余额、广告次数和最近设备。App 应在展示广告前检查：

```text
member.status == 1
member.is_black == false
```

### 3.4 获取用户奖励流水

`GET /mas/app/member/transactions?uid=U10001&page=1&limit=20&status=confirmed`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `uid` | 是 | 用户 ID |
| `page` | 否 | 页码，默认 1 |
| `limit` | 否 | 每页 1 至 100 条，默认 20 |
| `status` | 否 | `pending`、`confirmed`、`rejected`、`clawback` |

## 4. 广告位参数接口

### 4.1 获取 App 广告配置

`GET /mas/app/config`

返回当前后台绑定媒体的 TAKU App 参数、已开启广告位和公开风控配置。

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "config": {
      "ad_risk_enabled": "1",
      "daily_ad_limit": "50",
      "incentive_interval_seconds": "30",
      "device_daily_limit": "30",
      "ip_daily_limit": "100",
      "taku_app_key": "TAKU_APP_KEY"
    },
    "taku_apps": [
      {
        "app_id": "TAKU_APP_ID",
        "app_name": "Demo App",
        "platform": 2,
        "package_name": "com.example.app",
        "synced_at": "2026-07-23T12:00:00"
      }
    ],
    "taku_placements": [
      {
        "placement_id": "PLACEMENT_ID",
        "app_id": "TAKU_APP_ID",
        "placement_name": "聚合激励",
        "ad_format": "rewarded_video",
        "platform": "2"
      }
    ],
    "callback_urls": {
      "kuaishou": "/mas/callback/kuaishou/reward",
      "tencent": "/mas/callback/tencent/reward",
      "baidu": "/mas/callback/baidu/reward",
      "taku": "/mas/callback/taku/s2s"
    }
  }
}
```

广告类型：

| `ad_format` | 说明 |
| --- | --- |
| `splash` | 开屏 |
| `banner` | 横幅 |
| `rewarded_video` | 激励视频 |
| `interstitial` | 插屏 |
| `native` | 信息流 |

接口只返回当前媒体且状态为 `active` 的广告位。`taku_publisher_key` 和 `app_api_secret` 永远不会返回给 App。

## 5. 广告上报接口

### 5.1 广告展示前风控

`POST /mas/app/risk/precheck`

应在加载或展示激励广告前调用。

```json
{
  "uid": "U10001",
  "trans_id": "tx_20260723_001",
  "device_id": "idfa-or-oaid",
  "device_model": "iPhone 15",
  "device_unique_id": "idfa-or-oaid",
  "platform": 2,
  "ip": ""
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

只有 `passed=true` 时才应继续展示广告。

### 5.2 上报广告事件

`POST /mas/app/ad/event`

```json
{
  "uid": "U10001",
  "app_id": "TAKU_APP_ID",
  "app_name": "Demo App",
  "placement": "PLACEMENT_ID",
  "action": "show",
  "revenue": 0,
  "trans_id": "tx_20260723_001",
  "device_id": "idfa-or-oaid",
  "device_model": "iPhone 15",
  "device_unique_id": "idfa-or-oaid",
  "platform": 2,
  "ip": ""
}
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `uid` | 是 | 用户 ID |
| `app_id` | 否 | TAKU App ID |
| `app_name` | 否 | 应用名称 |
| `placement` | 否 | TAKU Placement ID |
| `action` | 否 | 默认 `show`，可传 `click`、`close`、`reward`、`error` |
| `revenue` | 否 | 客户端估算收益，默认 0 |
| `trans_id` | 否 | 广告事务 ID，激励广告建议必传 |
| `device_id` | 否 | 风控使用的设备 ID |
| `device_model` | 否 | 设备型号 |
| `device_unique_id` | 否 | IDFA、OAID 等唯一标识 |
| `platform` | 否 | 客户端平台 |
| `ip` | 否 | 通常留空，由服务端读取请求 IP |

该接口只记录客户端事件并执行风控，不直接发放奖励。

### 5.3 查询奖励状态

`GET /mas/app/reward/status?trans_id=tx_20260723_001&uid=U10001`

| 状态 | 说明 |
| --- | --- |
| `pending` | 等待广告平台或 TAKU 回调验证 |
| `confirmed` | 双方验证通过，奖励已确认 |
| `rejected` | 签名或风控未通过 |
| `clawback` | 对账核减 |

真实奖励由广告平台回调和 TAKU S2S 回调共同确认，App 上报不能替代服务端回调。

## 6. 服务端回调

以下接口由广告平台调用，不使用 App HMAC 签名：

| 平台 | 回调地址 |
| --- | --- |
| 快手 | `/mas/callback/kuaishou/reward` |
| 腾讯优量汇 | `/mas/callback/tencent/reward` |
| 百度广告 | `/mas/callback/baidu/reward` |
| TAKU S2S | `/mas/callback/taku/s2s` |

平台回调和 TAKU S2S 回调应携带相同的事务 ID，后台才能完成双重验证。

## 7. 常见错误

| 错误 | 说明 |
| --- | --- |
| `app_signature_headers_required` | 缺少签名 Header |
| `app_key_invalid` | `X-App-Key` 不正确 |
| `app_api_secret_not_configured` | 服务端未配置签名密钥 |
| `app_timestamp_invalid` | 时间戳格式错误 |
| `app_timestamp_expired` | 时间戳超出允许窗口 |
| `app_nonce_replayed` | Nonce 重复使用 |
| `app_signature_invalid` | HMAC 签名不正确 |
| `uid_required` | 缺少用户 ID |
| `member_not_found` | 用户不存在 |
| `transaction_not_found` | 奖励事务不存在 |
