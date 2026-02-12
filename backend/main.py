from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import market

import os

app = FastAPI(title="Trading Bot API", version="0.1.0")

# CORS setup
env_origins = os.getenv("CORS_ORIGINS", "")
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if env_origins:
    origins.extend([o.strip() for o in env_origins.split(",")])


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Trading Bot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
