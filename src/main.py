from fastapi import FastAPI

from pasteforge.core.loggers import setup_api_logging

setup_api_logging()  # Keep above others

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
