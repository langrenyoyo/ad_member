from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(64), default="管理员")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(64), default="")
    mobile: Mapped[str] = mapped_column(String(20), default="")
    agent_type: Mapped[int] = mapped_column(Integer, default=0)  # 0普通 1代理
    level_id: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[int] = mapped_column(Integer, default=1)  # 1正常 0冻结
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    today_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_balance: Mapped[float] = mapped_column(Float, default=0.0)
    confirmed_balance: Mapped[float] = mapped_column(Float, default=0.0)
    withdrawable_balance: Mapped[float] = mapped_column(Float, default=0.0)
    pending_balance: Mapped[float] = mapped_column(Float, default=0.0)
    device_model: Mapped[str] = mapped_column(String(128), default="")
    device_unique_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    ad_count: Mapped[int] = mapped_column(Integer, default=0)
    is_black: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DistributionLevel(Base):
    __tablename__ = "distribution_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    rate: Mapped[float] = mapped_column(Float, default=0.5)


class WhiteList(Base):
    __tablename__ = "white_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), index=True)
    remark: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdLog(Base):
    __tablename__ = "ad_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), index=True)
    app_name: Mapped[str] = mapped_column(String(128), default="")
    placement: Mapped[str] = mapped_column(String(128), default="")
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    action: Mapped[str] = mapped_column(String(32), default="show")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ContainmentLog(Base):
    __tablename__ = "containment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(64), default="block")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TakuApp(Base):
    __tablename__ = "taku_apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[str] = mapped_column(String(64), unique=True)
    app_name: Mapped[str] = mapped_column(String(128))
    platform: Mapped[int] = mapped_column(Integer, default=2)  # 1Android 2iOS
    package_name: Mapped[str] = mapped_column(String(128), default="")
    kuaishou_security_key: Mapped[str] = mapped_column(String(128), default="")
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[str] = mapped_column(Text, default="")


class IncentiveTransaction(Base):
    """激励事务：快手主验 + Taku 辅验，pending → confirmed / clawback。"""

    __tablename__ = "incentive_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trans_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    uid: Mapped[str] = mapped_column(String(32), index=True)
    app_id: Mapped[str] = mapped_column(String(64), default="")
    placement_id: Mapped[str] = mapped_column(String(64), default="")
    network_firm_id: Mapped[int] = mapped_column(Integer, default=28)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    user_reward: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    kuaishou_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    taku_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    kuaishou_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    taku_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_id: Mapped[str] = mapped_column(String(128), default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CallbackLog(Base):
    __tablename__ = "callback_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(16), index=True)
    trans_id: Mapped[str] = mapped_column(String(128), index=True, default="")
    sign_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReconcileDaily(Base):
    __tablename__ = "reconcile_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    estimated_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    confirmed_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    taku_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    kuaishou_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    gap_amount: Mapped[float] = mapped_column(Float, default=0.0)
    gap_rate: Mapped[float] = mapped_column(Float, default=0.0)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    confirmed_count: Mapped[int] = mapped_column(Integer, default=0)
    clawback_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskDecisionLog(Base):
    __tablename__ = "risk_decision_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), index=True)
    trans_id: Mapped[str] = mapped_column(String(128), default="")
    rule_name: Mapped[str] = mapped_column(String(64))
    score_delta: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(16), default="pass")
    detail: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemberDevice(Base):
    """用户设备型号与唯一标识绑定记录。"""

    __tablename__ = "member_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), index=True)
    device_model: Mapped[str] = mapped_column(String(128), default="")
    device_unique_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    platform: Mapped[int] = mapped_column(Integer, default=0)  # 0未知 1Android 2iOS
    source: Mapped[str] = mapped_column(String(32), default="client")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
