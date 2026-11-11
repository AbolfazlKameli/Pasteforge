from fastapi import FastAPI
from redis_fastapi import FastAPIRedis

from pasteforge.api.middlewares import CSRFMiddleware
from pasteforge.api.v1.router import router as api_v1_router
from pasteforge.core.exceptions import register_exception_handlers
from pasteforge.core.loggers import setup_api_logging  # noqa

app = FastAPI(
    title="PasteForge",
    summary="A lightweight Pastebin service focused on clean architecture, reliable data handling, and well-designed APIs.",  # noqa: E501
    version="0.4.0",
    contact={
        "name": "Abolfazl Kameli",
        "url": "https://github.com/abolfazlkameli",
        "email": "abolfazlkameli0@gmail.com",
    },
    license_info={"name": "MIT License", "url": "https://github.com/AbolfazlKameli/Pasteforge/blob/main/LICENSE"},
)

FastAPIRedis(app).lifespan().rate_limiting().caching()

app.include_router(api_v1_router)

app.add_middleware(CSRFMiddleware)

register_exception_handlers(app)
