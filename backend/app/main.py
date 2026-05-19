from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.database import engine, Base
from app.api.routers import auth, users, projects, risk_modules, test_items, checklists, operation_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    logger.info("创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表创建完成")
    yield
    await engine.dispose()


app = FastAPI(
    title="评审前风险自检系统 API",
    version="1.0.0",
    description="PRRC - Pre-Review Risk Checklist System",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"code": 500, "message": f"服务器内部错误: {str(exc)}"})


# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(risk_modules.router, prefix="/api/v1")
app.include_router(test_items.router, prefix="/api/v1")

app.include_router(checklists.router, prefix="/api/v1")
app.include_router(operation_logs.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
