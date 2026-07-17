# -*- coding: utf-8 -*-
"""
db_manager.py
مدير قاعدة البيانات - Database Manager
يوفر اتصال موحد بقاعدة بيانات SQLite وينفّذ الاستعلامات، كما يقوم بتهيئة
الـ schema تلقائيًا عند أول تشغيل (safe لأنه يستخدم CREATE TABLE IF NOT EXISTS).
"""
import os
import sqlite3


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_schema()
        # أضف هذا الجزء في نهاية دالة تهيئة الجداول داخل db_manager.py
        try:
            # محاولة إضافة عمود تاريخ البداية في حال عدم وجوده
            self.execute("ALTER TABLE committees ADD COLUMN start_date TEXT DEFAULT '2026-01-01';")
            # محاولة إضافة عمود تاريخ النهاية في حال عدم وجوده
            self.execute("ALTER TABLE committees ADD COLUMN end_date TEXT;")
            
            # تحديث جدول أعضاء اللجان لإضافة حقول المسمى الوظيفي والماليات (في حال عدم وجودها)
            self.execute("ALTER TABLE committee_members ADD COLUMN role TEXT DEFAULT 'عضو لجنة';")
            self.execute("ALTER TABLE committee_members ADD COLUMN attendance_allowance REAL DEFAULT 0.0;")
            self.execute("ALTER TABLE committee_members ADD COLUMN bonus_amount REAL DEFAULT 0.0;")
        except Exception as e:
            # إذا كانت الأعمدة مضافة مسبقاً، سيفشل الأمر في SQLite وينتقل البرنامج هنا فوراً بسلام
            pass

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        """تنفيذ ملف schema.sql عند بدء التشغيل (idempotent)."""
        try:
            from config import resource_path
            schema_path = resource_path(os.path.join("database", "schema.sql"))
        except ImportError:
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn = self._get_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

    def execute(self, query, params=(), commit=False, fetchone=False, fetchall=False):
        """
        تنفيذ استعلام عام.
        - commit=True: لعمليات INSERT/UPDATE/DELETE (يرجع lastrowid)
        - fetchone / fetchall: لاستعلامات SELECT
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            result = None
            if fetchone:
                result = cur.fetchone()
            elif fetchall:
                result = cur.fetchall()
            if commit:
                conn.commit()
            last_id = cur.lastrowid
            return result if (fetchone or fetchall) else last_id
        finally:
            conn.close()

    def executemany(self, query, seq_of_params, commit=True):
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.executemany(query, seq_of_params)
            if commit:
                conn.commit()
        finally:
            conn.close()
