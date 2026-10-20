from fastapi import FastAPI

from src.pasteforge.core.loggers import setup_api_logging

setup_api_logging()  # Keep above others

app = FastAPI(
    title='PasteForge',
    summary='A lightweight Pastebin service focused on clean architecture, reliable data handling, and well-designed APIs.',
    version='0.1.0',
    contact={
        'name': 'Abolfazl Kameli',
        'url': 'https://github.com/abolfazlkameli',
        'email': 'abolfazlkameli0@gmail.com'
    },
    license_info={
        'name': 'MIT License',
        'url': 'https://github.com/AbolfazlKameli/Pasteforge/blob/main/LICENSE'
    },
)


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello/{name}')
async def say_hello(name: str):
    return {'message': f'Hello {name}'}
