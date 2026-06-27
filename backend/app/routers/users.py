"""
Users Router — Kullanıcı profili ve istatistikleri.

Curl Örnekleri:
--------------
# Kullanıcı profili getir
curl "http://localhost:8000/users/user-a-0001?viewer_id=user-b-0002"

# Kullanıcı istatistikleri getir
curl "http://localhost:8000/users/user-a-0001/stats"
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.database import get_db
from app.models import UserResponse, UserStatsResponse

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    viewer_id: Optional[str] = Query(None, description="Görüntüleyen kullanıcı ID"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Kullanıcı profil bilgisini döndürür. is_following bilgisi viewer'a göre hesaplanır."""
    try:
        row = db.execute(
            """
            SELECT user_id, username, display_name, avatar_url, bio,
                   followers_count, following_count, created_at
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        # is_following kontrolü
        is_following = False
        if viewer_id and viewer_id != user_id:
            follow_check = db.execute(
                "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?",
                (viewer_id, user_id),
            ).fetchone()
            is_following = follow_check is not None

        return UserResponse(
            user_id=row["user_id"],
            username=row["username"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            bio=row["bio"],
            followers_count=row["followers_count"],
            following_count=row["following_count"],
            created_at=row["created_at"],
            is_following=is_following,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kullanıcı getirilirken hata: {str(e)}")


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def get_user_stats(user_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Kullanıcı istatistiklerini döndürür: takipçi, takip, post sayıları."""
    try:
        row = db.execute(
            """
            SELECT u.user_id, u.followers_count, u.following_count,
                   (SELECT COUNT(*) FROM posts WHERE user_id = u.user_id) AS posts_count
            FROM users u
            WHERE u.user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        return UserStatsResponse(
            user_id=row["user_id"],
            followers_count=row["followers_count"],
            following_count=row["following_count"],
            posts_count=row["posts_count"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İstatistikler getirilirken hata: {str(e)}")
