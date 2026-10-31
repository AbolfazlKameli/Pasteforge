from fastapi import APIRouter

from pasteforge.api.v1.routers import auth, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
