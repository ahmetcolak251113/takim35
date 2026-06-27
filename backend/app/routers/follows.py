"""
Follows Router — Takip etme / takipten çıkma.

Curl Örnekleri:
--------------
# Takip et
curl -X POST http://localhost:8000/follow \
  -H "Content-Type: application/json" \
  -d '{"follower_id": "user-c-0003", "following_id": "user-a-0001"}'

# Takipten çık
curl -X DELETE http://localhost:8000/follow \
  -H "Content-Type: application/json" \
  -d '{"follower_id": "user-c-0003", "following_id": "user-a-0001"}'
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models import FollowRequest, MessageResponse

router = APIRouter()


@router.post("/follow", response_model=MessageResponse, status_code=201)
def follow_user(req: FollowRequest, db: sqlite3.Connection = Depends(get_db)):
    """Bir kullanıcıyı takip eder. Sayaçları günceller."""
    try:
        # Kendini takip etme engeli
        if req.follower_id == req.following_id:
            raise HTTPException(status_code=400, detail="Kendinizi takip edemezsiniz")

        # Kullanıcılar var mı?
        follower = db.execute("SELECT user_id FROM users WHERE user_id = ?", (req.follower_id,)).fetchone()
        if not follower:
            raise HTTPException(status_code=404, detail="Takip eden kullanıcı bulunamadı")

        following = db.execute("SELECT user_id FROM users WHERE user_id = ?", (req.following_id,)).fetchone()
        if not following:
            raise HTTPException(status_code=404, detail="Takip edilecek kullanıcı bulunamadı")

        # Duplicate follow kontrolü
        existing = db.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?",
            (req.follower_id, req.following_id),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Zaten takip ediyorsunuz")

        # Takip kaydı oluştur
        db.execute(
            "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
            (req.follower_id, req.following_id),
        )

        # Sayaçları güncelle
        db.execute(
            "UPDATE users SET following_count = following_count + 1 WHERE user_id = ?",
            (req.follower_id,),
        )
        db.execute(
            "UPDATE users SET followers_count = followers_count + 1 WHERE user_id = ?",
            (req.following_id,),
        )

        db.commit()

        return MessageResponse(success=True, message="Takip başarılı")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Takip işlemi sırasında hata: {str(e)}")


@router.delete("/follow", response_model=MessageResponse)
def unfollow_user(req: FollowRequest, db: sqlite3.Connection = Depends(get_db)):
    """Bir kullanıcıyı takipten çıkarır. Sayaçları günceller."""
    try:
        # Kendini takipten çıkma engeli
        if req.follower_id == req.following_id:
            raise HTTPException(status_code=400, detail="Kendinizi takipten çıkamazsınız")

        # Takip kaydı var mı?
        existing = db.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?",
            (req.follower_id, req.following_id),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Takip kaydı bulunamadı")

        # Takip kaydını sil
        db.execute(
            "DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
            (req.follower_id, req.following_id),
        )

        # Sayaçları güncelle
        db.execute(
            "UPDATE users SET following_count = MAX(0, following_count - 1) WHERE user_id = ?",
            (req.follower_id,),
        )
        db.execute(
            "UPDATE users SET followers_count = MAX(0, followers_count - 1) WHERE user_id = ?",
            (req.following_id,),
        )

        db.commit()

        return MessageResponse(success=True, message="Takipten çıkma başarılı")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Takipten çıkma sırasında hata: {str(e)}")
