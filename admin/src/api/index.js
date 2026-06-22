import request from './request'

export const login = (data) => request.post('/login/index', data)
export const logout = () => request.get('/login/logout')
export const getAdminInfo = () => request.get('/auth.admin/getAdminInfo')

export const getOverview = () => request.get('/index/index')
export const getActiveMembers = (time) => request.get('/index/member', { params: { time } })

export const getMemberList = (params) => request.get('/member/index', { params })
export const getMemberDevices = (uid) => request.get('/member/devices', { params: { uid } })
export const bindMemberDevice = (data) => request.post('/member/device/bind', data)
export const getMemberEdit = (uid) => request.get('/member/edit', { params: { uid } })
export const getMemberPromotion = (params) => request.get('/member/promotion', { params })
export const getMemberAdverLog = (params) => request.get('/member/more_adver_log', { params })
export const blacklistMember = (uid) => request.get('/member/toblack', { params: { uid } })
export const openMember = (uid) => request.post('/distribution.distribution_member/open', { uid })
export const freezeMember = (uid) => request.post('/distribution.distribution_member/freeze', { uid })
export const getLevelList = () => request.get('/distribution.distribution_level/lists')

export const getDailyReport = (params) => request.get('/adandrisk/dailyreport', { params })
export const getAdverLog = (params) => request.get('/adandrisk/adver_log', { params })
export const getContainmentLog = (params) => request.get('/adandrisk/containment_log', { params })

export const getTakuApps = () => request.get('/core/cron/takuapps')
export const syncTakuApp = (data) => request.post('/core/cron/takuapps/sync', data)
export const getConfig = () => request.get('/config/index')
export const saveConfig = (configs) => request.post('/config/ConfigSaveAll', { configs })

export const getRiskConfig = () => request.get('/risk/config')
export const saveRiskConfig = (configs) => request.post('/risk/config/save', { configs })
export const getIncentiveTransactions = (params) => request.get('/risk/transactions', { params })
export const getCallbackLogs = (params) => request.get('/risk/callback_logs', { params })
export const getRiskDecisions = (params) => request.get('/risk/decisions', { params })
export const getReconcileDaily = (params) => request.get('/risk/reconcile/daily', { params })
export const runReconcile = (date) => request.post('/risk/reconcile/run', { date })

export const getClawbackSummary = (params) => request.get('/risk/clawback/summary', { params })
export const getClawbackUsers = (params) => request.get('/risk/clawback/users', { params })
export const getClawbackDetail = (params) => request.get('/risk/clawback/detail', { params })
