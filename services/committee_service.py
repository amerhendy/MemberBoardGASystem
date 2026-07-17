# -*- coding: utf-8 -*-
"""
committee_service.py
خدمة إدارة اللجان المطورة - Committee Service
يدعم تواريخ عمل اللجان، البدلات والمكافآت للأعضاء، والتحويل التلقائي للحالة بناءً على التاريخ الحالي.
"""
from datetime import date

class CommitteeService:
    def __init__(self, db):
        self.db = db

    def auto_check_expired_committees(self):
        """
        تحديث تلقائي: تحويل أي لجنة انتهى تاريخ صلاحيتها (end_date < تاريخ اليوم) 
        إلى حالة غير نشطة (is_active = 0) أوتوماتيكياً.
        """
        today_str = date.today().isoformat()
        self.db.execute(
            "UPDATE committees SET is_active = 0 WHERE is_active = 1 AND end_date IS NOT NULL AND end_date < ?",
            (today_str,), commit=True
        )

    # ---------- اللجان ----------
    def create_committee(self, name, category, start_date, end_date=None, description=None, is_active=1):
        return self.db.execute(
            """INSERT INTO committees (name, category, start_date, end_date, description, is_active) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, category, start_date, end_date, description, is_active), commit=True,
        )

    def update_committee(self, committee_id, name, category, start_date, end_date=None, description=None, is_active=1):
        """تحديث بيانات اللجنة بالكامل وتحديث حالتها"""
        self.db.execute(
            """UPDATE committees 
               SET name = ?, category = ?, start_date = ?, end_date = ?, description = ?, is_active = ?
               WHERE id = ?""",
            (name, category, start_date, end_date, description, is_active, committee_id), commit=True
        )
        # تشغيل الفحص التلقائي بعد التعديل لضمان المزامنة الفورية
        self.auto_check_expired_committees()

    def list_committees(self, category=None, active_only=False):
        """جلب اللجان مع تشغيل الفحص التلقائي لتواريخ الانتهاء أولاً"""
        self.auto_check_expired_committees()
        
        query = "SELECT * FROM committees WHERE 1=1"
        params = []
        if active_only:
            query += " AND is_active = 1"
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY is_active DESC, name"
        rows = self.db.execute(query, params, fetchall=True)
        return [dict(r) for r in rows]

    def toggle_committee_status(self, committee_id, current_status):
        """تغيير حالة اللجنة يدوياً (تنشيط / تعطيل)"""
        new_status = 0 if current_status == 1 else 1
        self.db.execute(
            "UPDATE committees SET is_active = ? WHERE id = ?", (new_status, committee_id), commit=True
        )
        if new_status == 1:
            self.auto_check_expired_committees()

    # ---------- عضوية اللجان والماليات ----------
    def add_member_to_committee(self, committee_id, member_id, start_date, end_date=None, role="", allowance=0.0, bonus=0.0):
        return self.db.execute(
            """INSERT INTO committee_members (committee_id, member_id, start_date, end_date, role, attendance_allowance, bonus_amount)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (committee_id, member_id, start_date, end_date, role, allowance, bonus), commit=True,
        )

    def update_committee_membership(self, cm_id, start_date, end_date=None, role="", allowance=0.0, bonus=0.0):
        """تعديل بيانات عضوية العضو والبدلات المالية الخاصة به في اللجنة"""
        self.db.execute(
            """UPDATE committee_members 
               SET start_date = ?, end_date = ?, role = ?, attendance_allowance = ?, bonus_amount = ?
               WHERE id = ?""",
            (start_date, end_date, role, allowance, bonus, cm_id), commit=True
        )

    def list_committee_members(self, committee_id):
        rows = self.db.execute(
            """SELECT cm.id as committee_member_id, cm.start_date, cm.end_date, cm.role, 
                      cm.attendance_allowance, cm.bonus_amount, m.id as member_real_id, m.*
               FROM committee_members cm
               JOIN members m ON m.id = cm.member_id
               WHERE cm.committee_id = ?
               ORDER BY m.full_name""",
            (committee_id,), fetchall=True,
        )
        return [dict(r) for r in rows]

    def remove_member_from_committee(self, cm_id):
        """حذف عضو من اللجنة نهائياً"""
        self.db.execute("DELETE FROM committee_members WHERE id = ?", (cm_id,), commit=True)