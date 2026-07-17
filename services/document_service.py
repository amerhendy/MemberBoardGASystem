# -*- coding: utf-8 -*-
"""
document_service.py
خدمة مستندات الأعضاء - Member Documents Service
تنسخ الملف المرفوع إلى ./member_documents/{Type}/{member_id}/ وتسجّله في القاعدة.
"""
import os
import shutil
import uuid

from config import DOCUMENTS_DIR


class DocumentService:
    def __init__(self, db):
        self.db = db

    def _target_dir(self, member_type: str, member_id: int) -> str:
        target_dir = os.path.join(DOCUMENTS_DIR, member_type, str(member_id))
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def add_document(self, member_id: int, member_type: str, doc_type: str, source_path: str) -> int:
        """
        ينسخ الملف من source_path إلى مجلد العضو المخصص، ويحفظ سجل في القاعدة.
        يُستخدم اسم فريد (uuid) لتجنب تعارض الأسماء مع الحفاظ على الامتداد الأصلي.
        """
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"الملف غير موجود: {source_path}")

        target_dir = self._target_dir(member_type, member_id)
        original_name = os.path.basename(source_path)
        _, ext = os.path.splitext(original_name)
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest_path = os.path.join(target_dir, stored_name)

        shutil.copy2(source_path, dest_path)

        return self.db.execute(
            """INSERT INTO member_documents (member_id, doc_type, file_path, original_name)
               VALUES (?, ?, ?, ?)""",
            (member_id, doc_type, dest_path, original_name), commit=True,
        )

    def list_documents(self, member_id: int):
        rows = self.db.execute(
            "SELECT * FROM member_documents WHERE member_id = ? ORDER BY uploaded_at DESC",
            (member_id,), fetchall=True,
        )
        return [dict(r) for r in rows]

    def delete_document(self, document_id: int):
        row = self.db.execute(
            "SELECT file_path FROM member_documents WHERE id = ?", (document_id,), fetchone=True
        )
        if row and os.path.isfile(row["file_path"]):
            try:
                os.remove(row["file_path"])
            except OSError:
                pass
        self.db.execute("DELETE FROM member_documents WHERE id = ?", (document_id,), commit=True)
