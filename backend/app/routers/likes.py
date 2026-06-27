"""
Likes Router — Beğeni ekleme / kaldırma.

Curl Örnekleri:
--------------
# Beğen
curl -X POST http://localhost:8000/posts/post-0001/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-c-0003"}'

# Beğeniyi geri al
curl -X DELETE http://localhost:8000/posts/post-0001/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-c-0003"}'
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models import LikeRequest, MessageResponse

router = APIRouter()


@router.post("/posts/{post_id}/like", response_model=MessageResponse, status_code=201)
def like_post(post_id: str, req: LikeRequest, db: sqlite3.Connection = Depends(get_db)):
    """Bir postu beğenir. likes_count sayacını günceller."""
    try:
        # Post var mı?
        post = db.execute("SELECT post_id FROM posts WHERE post_id = ?", (post_id,)).fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post bulunamadı")

        # Kullanıcı var mı?
        user = db.execute("SELECT user_id FROM users WHERE user_id = ?", (req.user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        # Duplicate like kontrolü
        existing = db.execute(
            "SELECT 1 FROM likes WHERE post_id = ? AND user_id = ?",
            (post_id, req.user_id),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Bu postu zaten beğendiniz")

        # Like kaydı oluştur
        db.execute(
            "INSERT INTO likes (post_id, user_id) VALUES (?, ?)",
            (post_id, req.user_id),
        )

        # likes_count güncelle
        db.execute(
            "UPDATE posts SET likes_count = likes_count + 1 WHERE post_id = ?",
            (post_id,),
        )

        db.commit()

        return MessageResponse(success=True, message="Beğeni eklendi")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beğeni eklenirken hata: {str(e)}")


@router.delete("/posts/{post_id}/like", response_model=MessageResponse)
def unlike_post(post_id: str, req: LikeRequest, db: sqlite3.Connection = Depends(get_db)):
    """Bir postun beğenisini geri alır. likes_count sayacını günceller."""
    try:
        # Like kaydı var mı?
        existing = db.execute(
            "SELECT 1 FROM likes WHERE post_id = ? AND user_id = ?",
            (post_id, req.user_id),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Beğeni kaydı bulunamadı")

        # Like kaydını sil
        db.execute(
            "DELETE FROM likes WHERE post_id = ? AND user_id = ?",
            (post_id, req.user_id),
        )

        # likes_count güncelle
        db.execute(
            "UPDATE posts SET likes_count = MAX(0, likes_count - 1) WHERE post_id = ?",
            (post_id,),
        )

        db.commit()

        return MessageResponse(success=True, message="Beğeni kaldırıldı")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beğeni kaldırılırken hata: {str(e)}")
