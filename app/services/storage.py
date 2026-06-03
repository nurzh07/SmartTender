import os
from pathlib import Path

from app.config import get_settings

settings = get_settings()


def ensure_upload_dirs() -> None:
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOAD_DIR, "proposals").mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOAD_DIR, "reports").mkdir(parents=True, exist_ok=True)


def save_local_file(relative_path: str, content: bytes) -> str:
    ensure_upload_dirs()
    full_path = Path(settings.UPLOAD_DIR) / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)
    return str(full_path)


def save_report_file(filename: str, content: bytes) -> str:
    if settings.USE_MINIO:
        return _save_to_minio(f"reports/{filename}", content)
    path = save_local_file(f"reports/{filename}", content)
    return f"/api/reports/files/{filename}"


def save_proposal_file(tender_id: int, supplier_id: int, filename: str, content: bytes) -> str:
    safe_name = filename.replace("..", "").replace("/", "_")
    rel = f"proposals/{tender_id}/{supplier_id}_{safe_name}"
    if settings.USE_MINIO:
        return _save_to_minio(rel, content)
    save_local_file(rel, content)
    return rel


def _save_to_minio(key: str, content: bytes) -> str:
    try:
        from minio import Minio

        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
        import io

        client.put_object(
            settings.MINIO_BUCKET,
            key,
            io.BytesIO(content),
            length=len(content),
        )
        return f"minio://{settings.MINIO_BUCKET}/{key}"
    except Exception:
        return save_local_file(key, content)
