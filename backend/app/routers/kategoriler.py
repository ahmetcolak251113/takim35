"""
Kategoriler Router — Dolap formu için açılır menü seçenekleri.

Endpoint'ler:
  GET  /kategoriler              → Tüm kategoriler (dict)
  POST /kategoriler              → Yeni değer ekle
  POST /kategoriler/sil-deger   → Değer sil
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db

router = APIRouter()

GECERLI_TIPLER = {
    "tur", "kumas", "kesim", "yaka_tipi", "kol_tipi",
    "desen", "mevsim", "stil_etiketi", "kullanim_sikligi",
}


class KategoriEkle(BaseModel):
    tip: str
    deger: str


class KategoriSil(BaseModel):
    tip: str
    deger: str


@router.get("/kategoriler")
def kategorileri_getir(db: sqlite3.Connection = Depends(get_db)):
    """Tüm kategori değerlerini tip → [değer] formatında döner."""
    rows = db.execute(
        "SELECT tip, deger FROM kategori_degerleri ORDER BY tip, deger"
    ).fetchall()
    sonuc: dict = {tip: [] for tip in GECERLI_TIPLER}
    for row in rows:
        tip = row["tip"]
        if tip in sonuc:
            sonuc[tip].append(row["deger"])
    return sonuc


@router.post("/kategoriler", status_code=201)
def kategori_ekle(body: KategoriEkle, db: sqlite3.Connection = Depends(get_db)):
    """Kategoriye yeni değer ekle."""
    if body.tip not in GECERLI_TIPLER:
        raise HTTPException(status_code=400, detail=f"Geçersiz kategori tipi: {body.tip}")
    if not body.deger.strip():
        raise HTTPException(status_code=400, detail="Değer boş olamaz.")
    try:
        db.execute(
            "INSERT INTO kategori_degerleri (tip, deger) VALUES (?, ?)",
            (body.tip, body.deger.strip()),
        )
        return {"mesaj": f"'{body.deger}' eklendi."}
    except Exception:
        raise HTTPException(status_code=409, detail="Bu değer zaten mevcut.")


@router.post("/kategoriler/sil-deger")
def kategori_sil(body: KategoriSil, db: sqlite3.Connection = Depends(get_db)):
    """Kategoriden değer sil."""
    if body.tip not in GECERLI_TIPLER:
        raise HTTPException(status_code=400, detail=f"Geçersiz kategori tipi: {body.tip}")
    result = db.execute(
        "DELETE FROM kategori_degerleri WHERE tip=? AND deger=?",
        (body.tip, body.deger),
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Değer bulunamadı.")
    return {"mesaj": f"'{body.deger}' silindi."}
