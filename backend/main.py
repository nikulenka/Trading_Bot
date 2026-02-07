from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import market

app = FastAPI(title="Trading Bot API", version="0.1.0")

# CORS setup
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

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
