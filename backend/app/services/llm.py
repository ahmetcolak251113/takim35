"""
LLM Servis Katmanı — Provider bağımsız AI yanıt üretimi.

LLM_PROVIDER env değişkenine göre:
  - "ollama"  → Lokal Ollama HTTP API (varsayılan)
  - "gemini"  → Google Gemini API

Kullanım:
    from app.services.llm import get_llm_response
    yanit = await get_llm_response("Bugün ne giymeliyim?")
"""

import httpx
from typing import Optional
from app.config import settings


async def get_llm_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Yapılandırılan LLM provider'a göre yanıt üretir.

    Args:
        prompt: Kullanıcı mesajı / ana prompt
        system_prompt: Sistem promptu (opsiyonel)

    Returns:
        Model yanıtı string olarak. Hata durumunda boş string.
    """
    provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()

    if provider == "gemini":
        return await _gemini_response(prompt, system_prompt)
    else:
        return await _ollama_response(prompt, system_prompt)


# ── Ollama ──────────────────────────────────────────────────────────────────

async def _ollama_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Ollama HTTP API'sine istek atar."""
    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model = getattr(settings, "OLLAMA_MODEL", "llama3.2")

    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nKullanıcı: {prompt}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 512,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()

    except httpx.ConnectError:
        raise RuntimeError(
            "Ollama'ya bağlanılamadı. "
            "'ollama serve' komutunu çalıştırdığınızdan emin olun."
        )
    except httpx.TimeoutException:
        raise RuntimeError("Ollama yanıt vermedi (timeout). Model yükleniyor olabilir, tekrar deneyin.")
    except Exception as e:
        raise RuntimeError(f"Ollama hatası: {e}")


# ── Gemini ──────────────────────────────────────────────────────────────────

async def _gemini_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Google Gemini API'ye istek atar."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
        return ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = model.generate_content(full_prompt)
        return response.text.strip()

    except Exception as e:
        raise RuntimeError(f"Gemini hatası: {e}")
