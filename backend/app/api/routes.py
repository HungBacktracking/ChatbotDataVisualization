from fastapi import APIRouter

from app.api.endpoints.chat import router as chat_router

routers = APIRouter()
router_list = [
    chat_router
]

for router in router_list:
    router.tags = routers
    routers.include_router(router)
