/** 后台展示用：英文状态码 → 中文标签 */

const INCENTIVE_STATUS = {
  pending: { label: '待确认', type: 'warning' },
  confirmed: { label: '已确认', type: 'success' },
  clawback: { label: '已扣回', type: 'danger' },
  rejected: { label: '已拒绝', type: 'info' },
}

const RECONCILE_STATUS = {
  alert: { label: 'GAP 告警', type: 'danger' },
  done: { label: '已对账', type: 'success' },
  pending: { label: '待对账', type: 'warning' },
}

const RISK_ACTION = {
  block: { label: '拦截', type: 'danger' },
  pass: { label: '通过', type: 'success' },
}

const DEDUCTION_TYPE = {
  clawback: { label: '已扣回', type: 'danger' },
  rejected: { label: '风控拒绝', type: 'warning' },
  pending_lost: { label: '回调未齐', type: 'info' },
}

const AD_ACTION = {
  show: { label: '展示' },
  click: { label: '点击' },
  reward: { label: '奖励' },
}

const CALLBACK_SOURCE = {
  kuaishou: '快手',
  taku: 'Taku',
}

const DEVICE_SOURCE = {
  client: '客户端',
  callback: '回调',
  seed: '演示数据',
  kuaishou: '快手回调',
  taku: 'Taku回调',
}

const PLATFORM = {
  1: '安卓',
  2: 'iOS',
}

export function incentiveStatusLabel(status) {
  return INCENTIVE_STATUS[status]?.label ?? status
}

export function incentiveStatusType(status) {
  return INCENTIVE_STATUS[status]?.type ?? 'info'
}

export function reconcileStatusLabel(status) {
  return RECONCILE_STATUS[status]?.label ?? status
}

export function reconcileStatusType(status) {
  return RECONCILE_STATUS[status]?.type ?? 'info'
}

export function riskActionLabel(action) {
  return RISK_ACTION[action]?.label ?? action
}

export function riskActionType(action) {
  return RISK_ACTION[action]?.type ?? 'info'
}

export function deductionTypeLabel(type) {
  return DEDUCTION_TYPE[type]?.label ?? type
}

export function deductionTypeTag(type) {
  return DEDUCTION_TYPE[type]?.type ?? 'info'
}

export function adActionLabel(action) {
  return AD_ACTION[action]?.label ?? action
}

export function callbackSourceLabel(source) {
  return CALLBACK_SOURCE[source] ?? DEVICE_SOURCE[source] ?? source
}

export function deviceSourceLabel(source) {
  return DEVICE_SOURCE[source] ?? source
}

export function platformLabel(platform) {
  return PLATFORM[platform] ?? (platform ? String(platform) : '—')
}
