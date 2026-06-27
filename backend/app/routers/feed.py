"""
Feed Router — Cursor-based pagination ile takip edilen kullanıcıların postları.

Curl Örnekleri:
--------------
# Feed'i getir (ilk sayfa)
curl "http://localhost:8000/feed?user_id=user-b-0002&limit=20"

# Feed'i getir (sonraki sayfa, cursor ile)
curl "http://localhost:8000/feed?user_id=user-b-0002&cursor=2026-01-01T00:00:00.000Z|post-0001&limit=20"
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.database import get_db
from app.models import PostResponse, FeedResponse, OutfitItemResponse

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    user_id: str = Query(..., description="Feed sahibi kullanıcı ID"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (created_at|post_id)"),
    limit: int = Query(20, ge=1, le=100, description="Sayfa başına post sayısı"),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Takip edilen kullanıcıların postlarını cursor-based pagination ile döndürür.

    Visibility kuralları SQL seviyesinde:
    - public → herkese açık
    - followers → sadece takipçilere (follows tablosunda kayıt VARSA)
    - private → feed'de GÖSTERİLMEZ
    """
    try:
        # Kullanıcı var mı?
        user = db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        # Cursor parse
        cursor_conditions = ""
        params: list = [user_id, user_id]

        if cursor:
            try:
                cursor_created_at, cursor_post_id = cursor.rsplit("|", 1)
                cursor_conditions = "AND (p.created_at < ? OR (p.created_at = ? AND p.post_id < ?))"
                params.extend([cursor_created_at, cursor_created_at, cursor_post_id])
            except ValueError:
                raise HTTPException(status_code=400, detail="Geçersiz cursor formatı. Beklenen: created_at|post_id")

        # limit + 1 ile sonraki sayfa var mı kontrol et
        query = f"""
            SELECT p.*, u.username, u.display_name, u.avatar_url
            FROM posts p
            JOIN users u ON p.user_id = u.user_id
            JOIN follows f ON f.following_id = p.user_id AND f.follower_id = ?
            WHERE p.visibility IN ('public', 'followers')
              AND (
                p.visibility = 'public'
                OR (
                  p.visibility = 'followers'
                  AND EXISTS (
                    SELECT 1 FROM follows
                    WHERE follower_id = ? AND following_id = p.user_id
                  )
                )
              )
              {cursor_conditions}
            ORDER BY p.created_at DESC, p.post_id DESC
            LIMIT ?
        """
        params.append(limit + 1)

        rows = db.execute(query, params).fetchall()

        # Sonraki sayfa var mı?
        has_next = len(rows) > limit
        if has_next:
            rows = rows[:limit]

        # Post'ları dönüştür
        posts = []
        for row in rows:
            # is_liked kontrolü
            like_check = db.execute(
                "SELECT 1 FROM likes WHERE post_id = ? AND user_id = ?",
                (row["post_id"], user_id),
            ).fetchone()
            is_liked = like_check is not None

            # Outfit items
            outfit_rows = db.execute(
                "SELECT item_id, category, image_url FROM post_outfit_items WHERE post_id = ?",
                (row["post_id"],),
            ).fetchall()
            outfit_items = [
                OutfitItemResponse(
                    item_id=oi["item_id"],
                    category=oi["category"],
                    image_url=oi["image_url"],
                )
                for oi in outfit_rows
            ]

            posts.append(
                PostResponse(
                    post_id=row["post_id"],
                    user_id=row["user_id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    avatar_url=row["avatar_url"],
                    image_url=row["image_url"],
                    caption=row["caption"],
                    visibility=row["visibility"],
                    ai_training_consent=bool(row["ai_training_consent"]),
                    likes_count=row["likes_count"],
                    is_liked=is_liked,
                    outfit_items=outfit_items,
                    created_at=row["created_at"],
                )
            )

        # Next cursor
        next_cursor = None
        if has_next and posts:
            last = posts[-1]
            next_cursor = f"{last.created_at}|{last.post_id}"

        return FeedResponse(posts=posts, next_cursor=next_cursor)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feed getirilirken hata: {str(e)}")
