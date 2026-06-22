import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import (
    AdLog,
    Admin,
    ContainmentLog,
    DistributionLevel,
    IncentiveTransaction,
    Member,
    ReconcileDaily,
    RiskDecisionLog,
    MemberDevice,
    SystemConfig,
    TakuApp,
    WhiteList,
)
from .auth import hash_password


def seed(db: Session) -> None:
    if not db.query(Admin).first():
        _seed_initial(db)
    if db.query(IncentiveTransaction).count() == 0:
        _seed_incentive_demo(db)
    if db.query(MemberDevice).count() == 0:
        _seed_member_devices(db)


def _seed_initial(db: Session) -> None:
    db.add(Admin(username="admin", password=hash_password("123456"), name="管理员"))
    db.add(Admin(username="qdmin", password=hash_password("1234156"), name="qdmin"))

    levels = [
        DistributionLevel(name="普通用户", rate=0.3),
        DistributionLevel(name="代理", rate=0.5),
    ]
    db.add_all(levels)
    db.flush()

    apps = [
        TakuApp(
            app_id="a63f5cced466da",
            app_name="步律城市iOS",
            platform=2,
            package_name="com.bulvchengshi.ios",
            kuaishou_security_key="demo_kuaishou_key_ios",
        ),
        TakuApp(
            app_id="b640ae1464e7e9",
            app_name="步律城市Android",
            platform=1,
            package_name="com.bulvchengshi.android",
            kuaishou_security_key="demo_kuaishou_key_android",
        ),
    ]
    db.add_all(apps)

    configs = [
        SystemConfig(key="ad_risk_enabled", value="1"),
        SystemConfig(key="daily_ad_limit", value="50"),
        SystemConfig(key="min_withdraw", value="10"),
        SystemConfig(key="taku_publisher_key", value=""),
        SystemConfig(key="reward_share_rate", value="0.88"),
        SystemConfig(key="confirm_delay_days", value="1"),
        SystemConfig(key="gap_alert_rate", value="0.08"),
        SystemConfig(key="taku_wait_seconds", value="5"),
        SystemConfig(key="device_daily_limit", value="30"),
        SystemConfig(key="risk_block_score", value="70"),
        SystemConfig(key="ip_daily_limit", value="100"),
    ]
    db.add_all(configs)

    models = ["iPhone 15 Pro", "iPhone 14", "Redmi K70", "OPPO A58", "vivo Y78", "HUAWEI Mate 60"]
    uniques = ["oaid_demo_001", "idfa_demo_002", "", "oaid_demo_004", "", "idfa_demo_006"]
    now = datetime.utcnow()
    for i in range(1, 26):
        agent = 0 if i % 5 else 1
        reward = round(random.uniform(10, 500), 2)
        pending = round(random.uniform(0, 20), 2)
        confirmed = round(reward * 0.85, 2)
        withdrawable = round(confirmed * 0.7, 2)
        idx = (i - 1) % len(models)
        member = Member(
            uid=f"U{10000 + i}",
            nickname=f"用户{i}",
            mobile=f"138{random.randint(10000000, 99999999)}",
            agent_type=agent,
            level_id=1 if agent == 0 else 2,
            total_revenue=reward,
            today_revenue=round(random.uniform(0, 20), 2),
            estimated_balance=reward,
            confirmed_balance=confirmed,
            withdrawable_balance=withdrawable,
            pending_balance=pending,
            device_model=models[idx],
            device_unique_id=uniques[idx],
            ad_count=random.randint(5, 200),
            last_active=now - timedelta(hours=random.randint(0, 72)),
        )
        db.add(member)
        db.flush()
        db.add(MemberDevice(
            uid=member.uid,
            device_model=models[idx],
            device_unique_id=uniques[idx],
            platform=2 if "iPhone" in models[idx] else 1,
            source="seed",
            created_at=now,
            updated_at=now,
        ))
        for j in range(random.randint(2, 6)):
            db.add(AdLog(
                uid=member.uid,
                app_name=random.choice(["步律城市iOS", "步律城市Android"]),
                placement=random.choice(["激励视频", "插屏", "开屏", "Banner"]),
                revenue=round(random.uniform(0.01, 2.5), 4),
                action=random.choice(["show", "click", "reward"]),
                created_at=now - timedelta(hours=random.randint(0, 48)),
            ))

    db.add(WhiteList(uid="U10001", remark="测试白名单", status=1))
    db.add(ContainmentLog(uid="U10005", reason="异常点击频率", action="block"))
    db.commit()


def _seed_incentive_demo(db: Session) -> None:
    members = db.query(Member).limit(25).all()
    if not members:
        return

    now = datetime.utcnow()
    for member in members:
        for k in range(random.randint(1, 3)):
            roll = random.random()
            if roll < 0.15:
                status = "clawback"
                taku_ok = False
            elif roll < 0.25:
                status = "rejected"
                taku_ok = False
            elif roll < 0.45:
                status = "pending"
                taku_ok = False
            else:
                status = "confirmed"
                taku_ok = True
            rev = round(random.uniform(0.05, 3.0), 4)
            user_reward = round(rev * 0.88 * 0.3, 4)
            created = now - timedelta(hours=random.randint(1, 72))
            remark = ""
            if status == "clawback":
                remark = random.choice([
                    "对账核减：Taku辅验未通过",
                    "快手联盟无效流量核减",
                    "平台核减扣回",
                ])
            db.add(IncentiveTransaction(
                trans_id=f"KS{member.uid}_{k}_{random.randint(1000, 9999)}",
                uid=member.uid,
                app_id=random.choice(["a63f5cced466da", "b640ae1464e7e9"]),
                placement_id=f"pl_{random.randint(100, 999)}",
                revenue=rev,
                user_reward=user_reward,
                status=status,
                kuaishou_verified=True,
                taku_verified=taku_ok,
                kuaishou_at=created,
                taku_at=created + timedelta(seconds=2) if taku_ok else None,
                device_id=f"dev_{random.randint(10000, 99999)}",
                ip=f"192.168.{random.randint(1, 10)}.{random.randint(1, 200)}",
                risk_score=random.randint(0, 40) if status != "rejected" else random.randint(70, 95),
                risk_passed=status != "rejected",
                remark=remark,
                created_at=created,
                confirmed_at=created + timedelta(minutes=1) if status == "confirmed" else None,
            ))

    db.add(RiskDecisionLog(
        uid="U10005",
        trans_id="KSU10005_0_1234",
        rule_name="用户日激励超限",
        score_delta=40,
        total_score=75,
        action="block",
        detail="52/50",
    ))

    yesterday = (now - timedelta(days=1)).date().isoformat()
    if not db.query(ReconcileDaily).filter(ReconcileDaily.date == yesterday).first():
        db.add(ReconcileDaily(
            date=yesterday,
            estimated_revenue=128.5,
            confirmed_revenue=118.2,
            taku_revenue=125.0,
            kuaishou_revenue=128.5,
            gap_amount=10.3,
            gap_rate=0.0802,
            transaction_count=86,
            confirmed_count=78,
            clawback_amount=2.1,
            status="alert",
        ))
    db.commit()


def _seed_member_devices(db: Session) -> None:
    """为已有用户补充演示设备绑定数据。"""
    models = ["iPhone 15 Pro", "iPhone 14", "Redmi K70", "OPPO A58", "vivo Y78", "HUAWEI Mate 60"]
    uniques = ["oaid_demo_001", "idfa_demo_002", "", "oaid_demo_004", "", "idfa_demo_006"]
    now = datetime.utcnow()
    for i, member in enumerate(db.query(Member).all()):
        idx = i % len(models)
        model = member.device_model or models[idx]
        unique = member.device_unique_id or uniques[idx]
        member.device_model = model
        member.device_unique_id = unique
        db.add(MemberDevice(
            uid=member.uid,
            device_model=model,
            device_unique_id=unique,
            platform=2 if "iPhone" in model else 1,
            source="seed",
            created_at=now,
            updated_at=now,
        ))
    db.commit()
