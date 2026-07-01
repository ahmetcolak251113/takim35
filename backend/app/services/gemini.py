"""
Gemini AI Servisi — Caption önerisi.

Curl Örnekleri:
--------------
# Caption önerisi al
curl -X POST http://localhost:8000/captions/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "outfit_items": [
      {"category": "üst giyim", "name": "Siyah blazer"},
      {"category": "alt giyim", "name": "Beyaz pantolon"},
      {"category": "ayakkabı", "name": "Kırmızı stiletto"}
    ],
    "style_hint": "iş kombini"
  }'
"""

from fastapi import APIRouter, HTTPException
from app.models import CaptionRequest, MessageResponse
from app.config import settings

router = APIRouter()


async def generate_caption(outfit_items: list[dict], style_hint: str = "") -> str:
    """
    Gemini API kullanarak kombin için caption önerisi üretir.

    Args:
        outfit_items: Kombin parçaları listesi (her biri dict: {category, name, ...})
        style_hint: Stil ipucu (opsiyonel)

    Returns:
        Üretilen caption string'i. Hata durumunda boş string.
    """
    if not settings.GEMINI_API_KEY:
        return ""

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Prompt oluştur
        items_desc = ", ".join(
            [f"{item.get('category', 'parça')}: {item.get('name', 'bilinmiyor')}" for item in outfit_items]
        )

        prompt = (
            f"Bu kombin için kısa, çekici bir sosyal medya caption'ı yaz (Türkçe, max 280 karakter).\n"
            f"Kombin parçaları: {items_desc}\n"
        )
        if style_hint:
            prompt += f"Stil: {style_hint}\n"

        prompt += "Sadece caption'ı yaz, başka açıklama ekleme. Emoji kullanabilirsin."

        response = model.generate_content(prompt)
        return response.text.strip()[:280]

    except Exception:
        # Graceful degradation: hata olursa boş string dön
        return ""


@router.post("/suggest", response_model=MessageResponse)
async def suggest_caption(req: CaptionRequest):
    """Kombin için AI destekli caption önerisi üretir."""
    try:
        caption = await generate_caption(req.outfit_items, req.style_hint)

        if not caption:
            return MessageResponse(
                success=True,
                message="Caption önerisi üretilemedi (API key eksik veya hata oluştu)",
                data={"caption": ""},
            )

        return MessageResponse(
            success=True,
            message="Caption önerisi başarıyla üretildi",
            data={"caption": caption},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption önerisi üretilirken hata: {str(e)}")
