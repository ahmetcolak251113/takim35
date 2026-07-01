"""
Kıyafetler Router — Dolap CRUD işlemleri.

Endpoint'ler:
  POST   /kiyafetler              → Kıyafet ekle
  GET    /kiyafetler/{user_id}    → Kullanıcının tüm kıyafetleri
  GET    /kiyafetler/{user_id}/temiz → Sadece temizleri
  GET    /kiyafet/{id}            → Tek kıyafet
  PATCH  /kiyafet/{id}            → Kıyafet güncelle
  PATCH  /kiyafetler/{id}/durum   → Temiz/kirli durumu değiştir
  DELETE /kiyafet/{id}            → Kıyafet sil
"""

import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db

router = APIRouter()


# ── Pydantic Şemaları ────────────────────────────────────────────

class KiyafetEkle(BaseModel):
    user_id: str
    tur: str
    renk: str
    marka: Optional[str] = None
    beden: Optional[str] = None
    kumas: Optional[str] = None
    kesim: Optional[str] = None
    yaka_tipi: Optional[str] = None
    kol_tipi: Optional[str] = None
    desen: Optional[str] = None
    mevsim: Optional[str] = None
    stil_etiketi: Optional[str] = None
    kullanim_sikligi: Optional[str] = None
    kombin_notu: Optional[str] = None
    foto_url: Optional[str] = None
    temiz: bool = True


class KiyafetGuncelle(BaseModel):
    tur: Optional[str] = None
    renk: Optional[str] = None
    marka: Optional[str] = None
    beden: Optional[str] = None
    kumas: Optional[str] = None
    kesim: Optional[str] = None
    yaka_tipi: Optional[str] = None
    kol_tipi: Optional[str] = None
    desen: Optional[str] = None
    mevsim: Optional[str] = None
    stil_etiketi: Optional[str] = None
    kullanim_sikligi: Optional[str] = None
    kombin_notu: Optional[str] = None
    foto_url: Optional[str] = None
    temiz: Optional[bool] = None


class DurumGuncelle(BaseModel):
    temiz: bool


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d['temiz'] = bool(d.get('temiz', 1))
    return d


# ── Endpoint'ler ─────────────────────────────────────────────────

@router.post("/kiyafetler", status_code=201)
def kiyafet_ekle(body: KiyafetEkle, db: sqlite3.Connection = Depends(get_db)):
    """Yeni kıyafet ekle."""
    if not body.tur or not body.renk:
        raise HTTPException(status_code=400, detail="Tür ve renk zorunludur.")
    cur = db.execute("""
        INSERT INTO kiyafetler
          (user_id,tur,renk,marka,beden,kumas,kesim,yaka_tipi,kol_tipi,
           desen,mevsim,stil_etiketi,kullanim_sikligi,kombin_notu,foto_url,temiz)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (body.user_id, body.tur, body.renk, body.marka, body.beden,
          body.kumas, body.kesim, body.yaka_tipi, body.kol_tipi,
          body.desen, body.mevsim, body.stil_etiketi, body.kullanim_sikligi,
          body.kombin_notu, body.foto_url, int(body.temiz)))
    return {"id": cur.lastrowid, "mesaj": "Kıyafet eklendi."}


@router.get("/kiyafetler/{user_id}")
def kiyafetleri_listele(user_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Kullanıcının tüm kıyafetleri."""
    rows = db.execute(
        "SELECT * FROM kiyafetler WHERE user_id=? ORDER BY id DESC", (user_id,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/kiyafetler/{user_id}/temiz")
def temiz_kiyafetler(user_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Kullanıcının sadece temiz kıyafetleri."""
    rows = db.execute(
        "SELECT * FROM kiyafetler WHERE user_id=? AND temiz=1 ORDER BY id DESC", (user_id,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/kiyafet/{kiyafet_id}")
def kiyafet_getir(kiyafet_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Tek kıyafet detayı."""
    row = db.execute("SELECT * FROM kiyafetler WHERE id=?", (kiyafet_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kıyafet bulunamadı.")
    return _row_to_dict(row)


@router.patch("/kiyafet/{kiyafet_id}")
def kiyafet_guncelle(kiyafet_id: int, body: KiyafetGuncelle, db: sqlite3.Connection = Depends(get_db)):
    """Kıyafet bilgilerini güncelle."""
    row = db.execute("SELECT id FROM kiyafetler WHERE id=?", (kiyafet_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kıyafet bulunamadı.")

    guncellemeler = body.model_dump(exclude_none=True)
    if not guncellemeler:
        raise HTTPException(status_code=400, detail="Güncellenecek alan belirtilmedi.")

    if 'temiz' in guncellemeler:
        guncellemeler['temiz'] = int(guncellemeler['temiz'])

    set_clause = ", ".join(f"{k}=?" for k in guncellemeler)
    values = list(guncellemeler.values()) + [kiyafet_id]
    db.execute(f"UPDATE kiyafetler SET {set_clause} WHERE id=?", values)
    return {"mesaj": "Kıyafet güncellendi."}


@router.patch("/kiyafetler/{kiyafet_id}/durum")
def durum_guncelle(kiyafet_id: int, body: DurumGuncelle, db: sqlite3.Connection = Depends(get_db)):
    """Kıyafetin temiz/kirli durumunu değiştir."""
    row = db.execute("SELECT id FROM kiyafetler WHERE id=?", (kiyafet_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kıyafet bulunamadı.")
    db.execute("UPDATE kiyafetler SET temiz=? WHERE id=?", (int(body.temiz), kiyafet_id))
    return {"mesaj": "Durum güncellendi."}


@router.delete("/kiyafet/{kiyafet_id}")
def kiyafet_sil(kiyafet_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Kıyafeti sil."""
    row = db.execute("SELECT id FROM kiyafetler WHERE id=?", (kiyafet_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kıyafet bulunamadı.")
    db.execute("DELETE FROM kiyafetler WHERE id=?", (kiyafet_id,))
    return {"mesaj": "Kıyafet silindi."}
