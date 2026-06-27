"""
Firebase Storage Servisi — Upload URL ve public URL üretimi.

Not: Bu dosya şu an placeholder implementasyon içerir.
Gerçek Firebase SDK entegrasyonu için firebase-admin paketi gerekir.
"""

from app.config import settings


def generate_upload_url(user_id: str, post_id: str, filename: str) -> dict:
    """
    Firebase Storage için signed upload URL üretir.

    Args:
        user_id: Kullanıcı ID
        post_id: Post ID
        filename: Dosya adı

    Returns:
        dict: upload_url ve file_path bilgilerini içerir
    """
    bucket = settings.FIREBASE_BUCKET or "placeholder-bucket.appspot.com"
    file_path = f"users/{user_id}/posts/{post_id}/{filename}"

    # Placeholder: Gerçek implementasyonda firebase-admin SDK kullanılacak
    # from firebase_admin import storage
    # bucket_ref = storage.bucket(bucket)
    # blob = bucket_ref.blob(file_path)
    # url = blob.generate_signed_url(expiration=timedelta(minutes=15), method="PUT")

    upload_url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o?uploadType=media&name={file_path}"

    return {
        "upload_url": upload_url,
        "file_path": file_path,
        "bucket": bucket,
    }


def get_public_url(file_path: str) -> str:
    """
    Firebase Storage'daki dosyanın CDN URL'sini döndürür.

    Args:
        file_path: Storage'daki dosya yolu (ör. users/xxx/posts/yyy/image.jpg)

    Returns:
        CDN URL string'i
    """
    bucket = settings.FIREBASE_BUCKET or "placeholder-bucket.appspot.com"

    # Placeholder: Gerçek implementasyonda token bazlı URL olabilir
    return f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{file_path}?alt=media"
