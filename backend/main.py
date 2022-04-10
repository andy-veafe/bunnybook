import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from auth.api import auth_router
from avatar.api import avatar_router
from avatar.service import AvatarService
from chat.api import chat_router
from chat.service import ChatService
from comment.api import comment_router
from common import injection
from common.exceptions import HTTPExceptionJSON
from common.injection import injector, Cache
from config import cfg
from database.core import db
from notification.api import notification_router
from notification.manager import NotificationManager
from post.api import post_router
from profiles.api import profiles_router
from profiles.exceptions import UnexpectedRelationshipState
from pubsub.websocket import WebSockets

# 初始化 FastAPI APP
app = FastAPI()

# 添加 CORS 中间件
if not cfg.prod:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 添加路由
web_router = APIRouter(prefix="/web")
web_router.include_router(auth_router, tags=["Auth"])
web_router.include_router(post_router, tags=["Posts"])
web_router.include_router(comment_router, tags=["Comments"])
web_router.include_router(profiles_router, tags=["Profiles"])
web_router.include_router(notification_router, tags=["Notifications"])
web_router.include_router(chat_router, tags=["Chat"])
web_router.include_router(avatar_router, tags=["Avatar"])
injector.get(AvatarService)
app.mount("/web/avatars", StaticFiles(directory=cfg.avatar_data_folder), name="avatar")
app.include_router(web_router)


# 添加异常处理
@app.exception_handler(HTTPExceptionJSON)
async def http_exception_handler(request: Request, exc: HTTPExceptionJSON):
    json_data = jsonable_encoder(exc.data)
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={"message": exc.detail, "code": exc.code, "error": json_data},
    )


@app.exception_handler(UnexpectedRelationshipState)
async def unicorn_exception_handler(request: Request, exc: UnexpectedRelationshipState):
    return JSONResponse(
        status_code=400, content={"message": "UnexpectedRelationshipState"}
    )


# FastAPI 启动事件处理
@app.on_event("startup")
async def startup():

    # 初始化依赖注入图数据和多项服务
    await injection.configure()

    # 初始化接口限流器
    await FastAPILimiter.init(injector.get(Cache))

    # 添加 Socket.IO 路由
    ws = injector.get(WebSockets)
    ws.include_ws_router(injector.get(ChatService))
    ws.include_socketio(app, path="/ws")
    injector.get(NotificationManager).start()
    injector.get(ChatService).subscribe_to_on_connect()
    injector.get(NotificationManager).subscribe_to_on_connect()

    # 连接到数据库
    await db.connect()


# FastAPI 结束事件处理
@app.on_event("shutdown")
async def shutdown():

    # 关闭数据库连接
    await db.disconnect()


if __name__ == "__main__":
    uvicorn.run(app, log_level=cfg.fastapi_log_level)
