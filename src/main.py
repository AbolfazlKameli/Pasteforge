from fastapi import FastAPI

from pasteforge.api.v1.router import router as api_v1_router
from pasteforge.core.exceptions import register_exception_handlers
from pasteforge.core.loggers import setup_api_logging  # noqa

app = FastAPI(
    title="PasteForge",
    summary="A lightweight Pastebin service focused on clean architecture, reliable data handling, and well-designed APIs.",  # noqa: E501
    version="0.3.3",
    contact={
        "name": "Abolfazl Kameli",
        "url": "https://github.com/abolfazlkameli",
        "email": "abolfazlkameli0@gmail.com",
    },
    license_info={"name": "MIT License", "url": "https://github.com/AbolfazlKameli/Pasteforge/blob/main/LICENSE"},
)

app.include_router(api_v1_router)


register_exception_handlers(app)
