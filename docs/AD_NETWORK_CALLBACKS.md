# 广告平台回调接入

系统支持快手、腾讯优量汇和百度广告的服务端激励回调。所有平台事件需要使用同一个
`trans_id` 与 Taku S2S 回调关联，只有广告平台验签和 Taku 验证都通过后，激励事务才会确认。

## 回调地址

- 快手：`/mas/callback/kuaishou/reward`
- 腾讯优量汇：`/mas/callback/tencent/reward`
- 百度广告：`/mas/callback/baidu/reward`
- Taku：`/mas/callback/taku/s2s`

腾讯和百度回调接受 GET 查询参数或 POST JSON，标准字段如下：

| 字段 | 别名 | 必填 | 说明 |
| --- | --- | --- | --- |
| `trans_id` | `transId`, `transaction_id` | 是 | 全局唯一事件流水号 |
| `user_id` | `userId`, `uid` | 是 | 用户标识 |
| `app_id` | `appId` | 是 | Taku 应用 ID，用于选择回调密钥 |
| `placement_id` | `placementId`, `pos_id` | 否 | 广告位 |
| `revenue` | `amount`, `reward_amount` | 否 | 平台收入 |
| `device_id` | `deviceId`, `oaid` | 否 | 设备标识 |
| `sign` | `signature` | 是 | 请求签名 |

## 签名方式

每个应用在“广告联盟与风控 -> Taku 应用”中独立配置腾讯和百度的回调密钥及签名方式。

- `hmac_sha256`：`HMAC-SHA256(trans_id, secret)`
- `sha256_secret_colon_transid`：`SHA256(secret + ":" + trans_id)`
- `md5_secret_colon_transid`：`MD5(secret + ":" + trans_id)`
- `md5_canonical`：排除 `sign`、`signature` 后按字段名排序，组成查询串并计算
  `MD5(canonical + "&key=" + secret)`

控制台协议与上述方式不一致时，应在平台适配层增加对应算法，不得关闭验签。未配置密钥、
缺少流水号或签名无效的请求只写回调日志，不创建激励事务。

## 联调要求

1. 在应用配置中保存平台回调密钥和签名方式。
2. 将对应回调 URL 配置到广告平台控制台。
3. 客户端展示广告时传递稳定的用户 ID 和事务 ID。
4. 确认广告平台回调与 Taku S2S 回调携带相同事务 ID。
5. 在激励事务页面按平台筛选，核对“平台”和“Taku”两个验证状态。
