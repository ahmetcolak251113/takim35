"""
Posts Router — Post oluşturma ve profil postları.

Curl Örnekleri:
--------------
# Yeni post oluştur
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-a-0001",
    "image_url": "https://example.com/posts/new.jpg",
    "caption": "Yeni kombinom!",
    "outfit_items": ["item-blazer-001", "item-pantolon-001"],
    "visibility": "public",
    "ai_training_consent": true
  }'

# Profil postlarını getir (sahibi olarak)
curl "http://localhost:8000/posts/users/user-a-0001/posts?viewer_id=user-a-0001"

# Profil postlarını getir (takipçi olarak)
curl "http://localhost:8000/posts/users/user-a-0001/posts?viewer_id=user-b-0002"

# Profil postlarını getir (yabancı olarak)
curl "http://localhost:8000/posts/users/user-a-0001/posts?viewer_id=user-c-0003"
"""

import uuid
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.database import get_db
from app.models import PostCreate, PostResponse, OutfitItemResponse, MessageResponse

router = APIRouter()


@router.post("", response_model=MessageResponse, status_code=201)
def create_post(post: PostCreate, db: sqlite3.Connection = Depends(get_db)):
    """Yeni post oluşturur."""
    try:
        post_id = str(uuid.uuid4())

        # Kullanıcı var mı kontrol et
        user = db.execute("SELECT user_id FROM users WHERE user_id = ?", (post.user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        # Post'u oluştur
        db.execute(
            """
            INSERT INTO posts (post_id, user_id, image_url, caption, visibility, ai_training_consent)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                post.user_id,
                post.image_url,
                post.caption,
                post.visibility,
                1 if post.ai_training_consent else 0,
            ),
        )

        # Outfit items ekle
        for item_id in post.outfit_items:
            db.execute(
                """
                INSERT INTO post_outfit_items (post_id, item_id)
                VALUES (?, ?)
                """,
                (post_id, item_id),
            )

        db.commit()

        return MessageResponse(
            success=True,
            message="Post başarıyla oluşturuldu",
            data={"post_id": post_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Post oluşturulurken hata: {str(e)}")


@router.get(
    "/users/{user_id}/posts",
    response_model=list[PostResponse],
)
def get_user_posts(
    user_id: str,
    viewer_id: Optional[str] = Query(None, description="Görüntüleyen kullanıcı ID"),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Kullanıcının profil postlarını döndürür.
    Visibility kuralları SQL seviyesinde uygulanır:
    - viewer == owner → tüm postlar
    - viewer takipçi → public + followers
    - viewer diğer → sadece public
    """
    try:
        # Kullanıcı var mı kontrol et
        user = db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

        if viewer_id and viewer_id == user_id:
            # Owner: tüm postları gör
            rows = db.execute(
                """
                SELECT p.*, u.username, u.display_name, u.avatar_url
                FROM posts p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.user_id = ?
                ORDER BY p.created_at DESC
                """,
                (user_id,),
            ).fetchall()
        elif viewer_id:
            # Takipçi mi kontrol et ve buna göre filtrele
            rows = db.execute(
                """
                SELECT p.*, u.username, u.display_name, u.avatar_url
                FROM posts p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.user_id = ?
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
                ORDER BY p.created_at DESC
                """,
                (user_id, viewer_id),
            ).fetchall()
        else:
            # Anonim: sadece public
            rows = db.execute(
                """
                SELECT p.*, u.username, u.display_name, u.avatar_url
                FROM posts p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.user_id = ? AND p.visibility = 'public'
                ORDER BY p.created_at DESC
                """,
                (user_id,),
            ).fetchall()

        # Postları response modeline dönüştür
        posts = []
        for row in rows:
            # is_liked kontrolü
            is_liked = False
            if viewer_id:
                like_check = db.execute(
                    "SELECT 1 FROM likes WHERE post_id = ? AND user_id = ?",
                    (row["post_id"], viewer_id),
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

        return posts

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Postlar getirilirken hata: {str(e)}")
