"""
Kombin Router — AI destekli kıyafet kombinasyonu önerisi.

Endpoint'ler:
  POST /kombin/oner                    → Kombin önerisi al
  POST /kombin/{oneri_id}/geri-bildirim → Beğeni/beğenmeme kaydet
"""

import json
import random
import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.services.llm import get_llm_response

router = APIRouter()


class KombinIstek(BaseModel):
    user_id: str
    etkinlik: str
    hava_durumu: str
    stil_tercihi: Optional[str] = None


class GeriBildirim(BaseModel):
    begenildi: bool


@router.post("/kombin/oner")
async def kombin_oner(body: KombinIstek, db: sqlite3.Connection = Depends(get_db)):
    """Kullanıcının dolabından AI destekli kombin önerisi oluştur."""
    if not body.etkinlik or not body.hava_durumu:
        raise HTTPException(status_code=400, detail="Etkinlik ve hava durumu zorunludur.")

    # Kullanıcının temiz kıyafetlerini getir
    rows = db.execute(
        "SELECT * FROM kiyafetler WHERE user_id=? AND temiz=1 ORDER BY id DESC",
        (body.user_id,)
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Dolabınızda temiz kıyafet bulunamadı. Önce Dolap sekmesinden kıyafet ekleyin."
        )

    kiyafetler = [dict(r) for r in rows]

    # AI prompt oluştur
    satirlar = []
    for k in kiyafetler:
        marka_str = f", {k['marka']}" if k.get('marka') else ''
        mevsim_str = f", {k['mevsim']}" if k.get('mevsim') else ''
        stil_str = f", {k['stil_etiketi']}" if k.get('stil_etiketi') else ''
        satirlar.append(
            f"- ID:{k['id']} {k['tur']} ({k['renk']}){marka_str}{mevsim_str}{stil_str}"
        )
    k_listesi = "\n".join(satirlar)

    stil_eki = f", stil tercihi: {body.stil_tercihi}" if body.stil_tercihi else ""
    prompt = (
        f"Kullanıcının dolabındaki kıyafetler:\n{k_listesi}\n\n"
        f"Etkinlik: {body.etkinlik}\n"
        f"Hava: {body.hava_durumu}{stil_eki}\n\n"
        f"Bu etkinlik ve hava için en uygun 2-4 kıyafeti seç ve kombin oluştur. "
        f"Yanıtını şu formatta ver:\n"
        f"SEÇİLEN_IDLER: [virgülle ayrılmış ID numaraları]\n"
        f"AÇIKLAMA: [tek paragraf, neden bu kombini seçtiğini açıkla]"
    )

    try:
        ai_yanit = await get_llm_response(prompt)
    except Exception as e:
        ai_yanit = ""

    # AI yanıtından ID ve açıklama parse et
    secilen_ids = []
    aciklama = "Bu etkinlik için önerilen kombin hazır."

    if ai_yanit:
        for satir in ai_yanit.split('\n'):
            if 'SEÇİLEN_IDLER' in satir or 'SECILEN_IDLER' in satir or 'ID' in satir.upper():
                import re
                ids = re.findall(r'\d+', satir)
                secilen_ids = [int(i) for i in ids if any(k['id'] == int(i) for k in kiyafetler)]
            elif 'AÇIKLAMA' in satir or 'ACIKLAMA' in satir:
                aciklama = satir.split(':', 1)[-1].strip()

    # Fallback: AI ID bulamadıysa rastgele 2-3 kıyafet seç
    if not secilen_ids:
        random.shuffle(kiyafetler)
        secilen_ids = [k['id'] for k in kiyafetler[:min(3, len(kiyafetler))]]
        if not ai_yanit:
            aciklama = f"{body.etkinlik} için dolabınızdan seçilen kombinasyon."
        else:
            # Tüm yanıtı açıklama olarak kullan
            aciklama = ai_yanit[:300] if ai_yanit else aciklama

    secilen_kiyafetler = [k for k in kiyafetler if k['id'] in secilen_ids]

    # Öneriyi kaydet
    cur = db.execute(
        """INSERT INTO kombin_onerileri
           (user_id, etkinlik, hava_durumu, stil_tercihi, aciklama, kiyafet_idler)
           VALUES (?,?,?,?,?,?)""",
        (body.user_id, body.etkinlik, body.hava_durumu,
         body.stil_tercihi, aciklama, json.dumps(secilen_ids))
    )

    return {
        "oneri_id": cur.lastrowid,
        "aciklama": aciklama,
        "secilen_kiyafetler": [
            {"id": k["id"], "tur": k["tur"], "renk": k["renk"]}
            for k in secilen_kiyafetler
        ],
    }


@router.post("/kombin/{oneri_id}/geri-bildirim")
def geri_bildirim(oneri_id: int, body: GeriBildirim, db: sqlite3.Connection = Depends(get_db)):
    """Kombin önerisine geri bildirim kaydet."""
    row = db.execute("SELECT id FROM kombin_onerileri WHERE id=?", (oneri_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Öneri bulunamadı.")
    db.execute(
        "UPDATE kombin_onerileri SET begenildi=? WHERE id=?",
        (int(body.begenildi), oneri_id)
    )
    return {"mesaj": "Geri bildirim kaydedildi."}
