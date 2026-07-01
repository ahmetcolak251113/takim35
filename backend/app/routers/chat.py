"""
Chat Router — Akıllı Dolap AI Sohbet Asistanı.

Curl Örnekleri:
--------------
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "ahmet_colak", "mesaj": "Bugün ne giymeliyim?"}'
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.llm import get_llm_response

router = APIRouter()

SYSTEM_PROMPT = (
    "Sen bir moda ve kombin asistanısın. Kullanıcının dolabını düzenlemesine, "
    "kıyafet seçmesine ve kombin oluşturmasına yardımcı oluyorsun. "
    "Türkçe konuş, samimi ve yardımsever ol. Yanıtlarını kısa ve pratik tut."
)


class ChatRequest(BaseModel):
    """Sohbet isteği."""
    user_id: str
    mesaj: str


class ChatResponse(BaseModel):
    """Sohbet yanıtı."""
    response: str
    user_id: str


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Akıllı Dolap AI asistanı ile sohbet et."""
    if not req.mesaj.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz")

    try:
        yanit = await get_llm_response(req.mesaj, system_prompt=SYSTEM_PROMPT)

        if not yanit:
            yanit = "Üzgünüm, şu an yanıt üretemiyorum. Lütfen tekrar deneyin."

        return ChatResponse(response=yanit, user_id=req.user_id)

    except RuntimeError as e:
        err = str(e)
        # Bağlantı / kota hatalarında kullanıcıya anlamlı mesaj
        if "Ollama'ya bağlanılamadı" in err:
            return ChatResponse(
                response=(
                    "AI servisi şu an başlatılmamış. "
                    "Lütfen terminalde 'ollama serve' komutunu çalıştırın."
                ),
                user_id=req.user_id,
            )
        if "429" in err or "quota" in err.lower():
            return ChatResponse(
                response=(
                    "AI servisimiz şu an yoğun. "
                    "Lütfen birkaç dakika sonra tekrar deneyin."
                ),
                user_id=req.user_id,
            )
        raise HTTPException(status_code=500, detail=err)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beklenmeyen hata: {e}")
