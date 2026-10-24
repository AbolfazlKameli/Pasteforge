from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from pasteforge.core.loggers import setup_api_logging  # noqa
from pasteforge.routers import auth_router, users_router

app = FastAPI(
    title="PasteForge",
    summary="A lightweight Pastebin service focused on clean architecture, reliable data handling, and well-designed APIs.",  # noqa: E501
    version="0.3.1",
    contact={
        "name": "Abolfazl Kameli",
        "url": "https://github.com/abolfazlkameli",
        "email": "abolfazlkameli0@gmail.com",
    },
    license_info={"name": "MIT License", "url": "https://github.com/AbolfazlKameli/Pasteforge/blob/main/LICENSE"},
)

app.include_router(auth_router)
app.include_router(users_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        content={"data": {"errors": exc.detail}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
