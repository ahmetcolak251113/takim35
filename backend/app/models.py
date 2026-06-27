"""
Pydantic v2 modelleri — Request & Response şemaları.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


# ============================================================
# Request Modelleri
# ============================================================

class PostCreate(BaseModel):
    """Yeni post oluşturma isteği."""
    user_id: str
    image_url: str
    caption: str | None = None
    outfit_items: list[str] = Field(default_factory=list)  # item_id listesi
    visibility: Literal["public", "followers", "private"] = "public"
    ai_training_consent: bool = False


class FollowRequest(BaseModel):
    """Takip etme / takipten çıkma isteği."""
    follower_id: str
    following_id: str


class LikeRequest(BaseModel):
    """Beğeni isteği."""
    user_id: str


class CaptionRequest(BaseModel):
    """AI caption önerisi isteği."""
    outfit_items: list[dict] = Field(default_factory=list)
    style_hint: str = ""


# ============================================================
# Response Modelleri
# ============================================================

class UserResponse(BaseModel):
    """Kullanıcı profil bilgisi."""
    user_id: str
    username: str
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    followers_count: int = 0
    following_count: int = 0
    created_at: str
    is_following: bool = False  # viewer bu kullanıcıyı takip ediyor mu?


class OutfitItemResponse(BaseModel):
    """Post'a bağlı kombin parçası."""
    item_id: str
    category: str
    image_url: str | None = None


class PostResponse(BaseModel):
    """Tek bir post."""
    post_id: str
    user_id: str
    username: str = ""
    display_name: str = ""
    avatar_url: str | None = None
    image_url: str
    caption: str | None = None
    visibility: str = "public"
    ai_training_consent: bool = False
    likes_count: int = 0
    is_liked: bool = False  # viewer beğenmiş mi?
    outfit_items: list[OutfitItemResponse] = Field(default_factory=list)
    created_at: str


class FeedResponse(BaseModel):
    """Sayfalandırılmış feed yanıtı."""
    posts: list[PostResponse]
    next_cursor: str | None = None


class UserStatsResponse(BaseModel):
    """Kullanıcı istatistikleri."""
    user_id: str
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0


class MessageResponse(BaseModel):
    """Genel başarı/hata mesajı."""
    success: bool
    message: str
    data: dict | None = None
