"""
Dijital Gardrop — FastAPI ana uygulama.

Lifespan event'inde veritabanını başlatır.
CORS middleware ekler.
Tüm router'ları dahil eder.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import posts, feed, follows, likes, users
from app.services.gemini import router as captions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatılırken veritabanını oluşturur."""
    init_db()
    yield


app = FastAPI(
    title="Dijital Gardrop API",
    description="Dijital Gardrop sosyal medya modülü REST API'si",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları dahil et
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(feed.router, tags=["Feed"])
app.include_router(follows.router, tags=["Follows"])
app.include_router(likes.router, tags=["Likes"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(captions_router, prefix="/captions", tags=["Captions"])


@app.get("/", tags=["Health"])
def health_check():
    """Sağlık kontrolü endpoint'i."""
    return {
        "status": "healthy",
        "service": "dijital-gardrop-api",
        "version": "1.0.0",
    }
