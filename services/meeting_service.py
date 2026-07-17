# -*- coding: utf-8 -*-
"""
meeting_service.py
خدمة إدارة الاجتماعات والحضور - Meeting & Attendance Service
عند إنشاء جلسة (Board/Assembly) بتاريخ معين، توفر هذه الخدمة قائمة الأعضاء
"النشطين فعليًا" في ذلك التاريخ فقط (Seat-Based Logic)، ثم تسمح بتسجيل
الحضور/الغياب والمبلغ المصروف لكل عضو.
"""


class MeetingService:
    def __init__(self, db, member_service):
        self.db = db
        self.member_service = member_service

    # ---------- الاجتماعات ----------
    def create_meeting(self, name, category, session_type, meeting_date,
                        default_allowance=0.0, committee_id=None, notes=None):
        return self.db.execute(
            """INSERT INTO meetings
               (name, category, session_type, committee_id, meeting_date, default_allowance, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, category, session_type, committee_id, meeting_date, default_allowance, notes),
            commit=True,
        )

    def list_meetings(self, category=None, date_from=None, date_to=None):
        query = "SELECT * FROM meetings WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if date_from:
            query += " AND meeting_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND meeting_date <= ?"
            params.append(date_to)
        query += " ORDER BY meeting_date DESC"
        rows = self.db.execute(query, params, fetchall=True)
        return [dict(r) for r in rows]

    def get_meeting(self, meeting_id):
        row = self.db.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,), fetchone=True)
        return dict(row) if row else None

    def delete_meeting(self, meeting_id):
        self.db.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,), commit=True)

    # ---------- تشيك ليست الحضور الديناميكي ----------
    def get_eligible_members_for_meeting(self, meeting_id):
        """
        يُرجع الأعضاء المستحقين للحضور في هذه الجلسة (بناءً على الفئة والتاريخ)،
        مع دمج حالة الحضور المسجلة مسبقًا (إن وجدت).
        """
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return []

        eligible_members = self.member_service.active_members_on_date(
            meeting["category"], meeting["meeting_date"]
        )

        existing = self.db.execute(
            "SELECT * FROM attendance_financials WHERE meeting_id = ?",
            (meeting_id,), fetchall=True,
        )
        existing_by_member = {row["member_id"]: dict(row) for row in existing}

        result = []
        for member in eligible_members:
            record = existing_by_member.get(member["id"], {
                "attended": 0,
                "amount_paid": meeting["default_allowance"],
                "notes": None,
            })
            result.append({**member, **record})
        return result

    def save_attendance(self, meeting_id, member_id, attended: bool, amount_paid: float, notes=None):
        self.db.execute(
            """INSERT INTO attendance_financials
               (meeting_id, member_id, attended, amount_paid, paid_date, notes)
               VALUES (?, ?, ?, ?, datetime('now'), ?)
               ON CONFLICT(meeting_id, member_id) DO UPDATE SET
                   attended = excluded.attended,
                   amount_paid = excluded.amount_paid,
                   notes = excluded.notes,
                   paid_date = datetime('now')""",
            (meeting_id, member_id, int(attended), amount_paid, notes), commit=True,
        )

    def bulk_save_attendance(self, meeting_id, attendance_rows):
        """attendance_rows: [{member_id, attended, amount_paid, notes}, ...]"""
        for row in attendance_rows:
            self.save_attendance(
                meeting_id, row["member_id"], row["attended"],
                row["amount_paid"], row.get("notes"),
            )
