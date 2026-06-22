from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .database import Base, engine, SessionLocal
from .migrate import ensure_configs, run_migrations
from .seed import seed
from .services.config_service import DEFAULT_RISK_CONFIG
from .routers import login, index, member, adandrisk, core, callback, risk

ADMIN_DIST = Path(__file__).resolve().parent.parent.parent / "admin" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations()
    db = SessionLocal()
    try:
        ensure_configs(db, DEFAULT_RISK_CONFIG)
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="用户管理后台", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mas = FastAPI()
mas.include_router(login.router)
mas.include_router(index.router)
mas.include_router(member.router)
mas.include_router(adandrisk.router)
mas.include_router(core.router)
mas.include_router(callback.router)
mas.include_router(risk.router)

app.mount("/mas", mas)

if ADMIN_DIST.exists():
    def _admin_file(path: str) -> Path | None:
        if not path or path.endswith("/"):
            return None
        target = (ADMIN_DIST / path).resolve()
        try:
            target.relative_to(ADMIN_DIST.resolve())
        except ValueError:
            return None
        return target if target.is_file() else None

    @app.get("/")
    def admin_index():
        return FileResponse(ADMIN_DIST / "index.html")

    @app.get("/{full_path:path}")
    def admin_spa(full_path: str):
        # API 子应用未匹配到的 /mas/* 仍返回 404
        if full_path.startswith("mas/") or full_path == "mas":
            raise HTTPException(status_code=404, detail="Not Found")
        file = _admin_file(full_path)
        if file:
            return FileResponse(file)
        return FileResponse(ADMIN_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "service": "ad_member_admin",
            "api": "/mas/",
            "admin": "run npm run dev in admin/",
            "callbacks": {
                "kuaishou": "/mas/callback/kuaishou/reward",
                "taku": "/mas/callback/taku/s2s",
            },
        }
