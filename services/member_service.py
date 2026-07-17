# -*- coding: utf-8 -*-
"""
member_service.py
خدمة إدارة الأعضاء المطورة - Premium Member Service
- CRUD كامل مع ميزات الحماية والنزاهة المرجعية للبيانات.
- حماية ضد تكرار الأسماء بالخطأ مع معالجة ذكية للمسافات الزائدة (TRIM).
- منع حذف الأعضاء المرتبطين بسجلات حضور سابقة لحماية دقة التقارير.
"""


class MemberService:
    def __init__(self, db):
        self.db = db

    # ---------- Create ----------
    def create_member(self, full_name, member_type, organization=None,
                       start_date=None, end_date=None, notes=None, status="Active"):
        """ينشئ عضوًا جديدًا بعد التحقق من عدم تكرار الاسم لتجنب الأخطاء البشرية."""
        cleaned_name = " ".join(full_name.strip().split())
        if self.member_exists(cleaned_name):
            raise ValueError(f"العضو '{cleaned_name}' مسجل بالفعل في النظام.")

        return self.db.execute(
            """INSERT INTO members
               (full_name, member_type, organization, start_date, end_date, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cleaned_name, member_type, organization, start_date, end_date, status, notes),
            commit=True,
        )

    # ---------- Update ----------
    def update_member(self, member_id, **fields):
        """تعديل بيانات العضو مع فحص الاسم لمنع التكرار والتعارض."""
        if not fields:
            return

        # تنظيف وفحص الاسم إذا تم إرساله للتحديث لضمان عدم التكرار مع عضو آخر
        if "full_name" in fields and fields["full_name"]:
            # إزالة المسافات المزدوجة والزائدة من الأطراف
            cleaned_name = " ".join(fields["full_name"].strip().split())
            fields["full_name"] = cleaned_name
            
            # نمرر الـ member_id المستهدف للاستثناء من الفحص لكي لا يرى نفسه تكراراً
            if self.member_exists(cleaned_name, exclude_member_id=member_id):
                raise ValueError(f"الاسم الجديد '{cleaned_name}' مستخدم بالفعل لعضو آخر.")

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [member_id]
        
        self.db.execute(
            f"UPDATE members SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values, commit=True,
        )

    # ---------- Delete ----------
    def delete_member(self, member_id):
        """
        حذف عضو من النظام.
        يقوم أولاً بفحص جدول الحضور (attendance)؛ إذا وجد له أي حضور مسجل،
        يمنع الحذف نهائياً لحماية سلامة التقارير المالية والإدارية القديمة.
        """
        row = self.db.execute(
            "SELECT COUNT(*) as c FROM attendance WHERE member_id = ?",
            (member_id,), fetchone=True
        )
        if row and row["c"] > 0:
            raise PermissionError(
                "لا يمكن حذف هذا العضو لوجود سجلات حضور وجلسات مرتبطة به. "
                "ننصح بتعديل حالته إلى 'غير نشط' بدلاً من الحذف للحفاظ على تاريخ التقارير."
            )

        self.db.execute("DELETE FROM members WHERE id = ?", (member_id,), commit=True)

    # ---------- Read ----------
    def get_member(self, member_id):
        row = self.db.execute("SELECT * FROM members WHERE id = ?", (member_id,), fetchone=True)
        return dict(row) if row else None

    def list_members(self, member_type=None, status=None, search=None):
        """جلب قائمة الأعضاء مع حساب إجمالي المستحقات (المبالغ المدفوعة للاجتماعات + مكافآت اللجان)"""
        query = """
            SELECT m.*, 
                   (
                       SELECT IFNULL(SUM(af.amount_paid), 0.0) 
                       FROM attendance_financials af 
                       WHERE af.member_id = m.id
                   ) as total_meetings_paid,
                   (
                       SELECT IFNULL(SUM(cm.bonus_amount), 0.0) 
                       FROM committee_members cm 
                       WHERE cm.member_id = m.id
                   ) as total_bonuses,
                   (
                       (SELECT IFNULL(SUM(af.amount_paid), 0.0) FROM attendance_financials af WHERE af.member_id = m.id) +
                       (SELECT IFNULL(SUM(cm.bonus_amount), 0.0) FROM committee_members cm WHERE cm.member_id = m.id)
                   ) as total_allowances
            FROM members m
            WHERE 1=1
        """
        params = []
        if member_type:
            query += " AND m.member_type = ?"
            params.append(member_type)
        if status:
            query += " AND m.status = ?"
            params.append(status)
        if search:
            query += " AND m.full_name LIKE ?"
            params.append(f"%{search}%")
            
        query += " ORDER BY m.full_name"
        rows = self.db.execute(query, params, fetchall=True)
        return [dict(r) for r in rows]

    def active_members_on_date(self, member_type, on_date):
        """
        الأعضاء الذين كانوا نشطين فعليًا في on_date (Seat-Based).
        يُستخدم في شاشة الاجتماعات لعرض قائمة الحضور الديناميكية.
        """
        rows = self.db.execute(
            """SELECT * FROM members
               WHERE member_type = ?
                 AND start_date <= ?
                 AND (end_date IS NULL OR end_date >= ?)
               ORDER BY full_name""",
            (member_type, on_date, on_date), fetchall=True,
        )
        return [dict(r) for r in rows]

    def counts_by_type(self):
        """لإحصائيات KPI في الداشبورد."""
        rows = self.db.execute(
            """SELECT member_type, status, COUNT(*) as cnt
               FROM members GROUP BY member_type, status""",
            fetchall=True,
        )
        return [dict(r) for r in rows]

    # ---------- Helper Validation Methods ----------
    def member_exists(self, full_name: str, exclude_member_id: int = None) -> bool:
        """
        يتحقق من وجود الاسم مسبقاً في النظام *بشرط أن يكون العضو نشطاً (Active)*.
        هذا يسمح بإعادة تسجيل نفس العضو إذا كانت حالته السابقة غير نشطة،
        كما يمنع التكرار المزدوج للأعضاء النشطين في نفس الوقت.
        """
        cleaned_name = " ".join(full_name.strip().split())
        
        if exclude_member_id:
            row = self.db.execute(
                """SELECT id FROM members 
                   WHERE TRIM(full_name) = TRIM(?) 
                     AND status = 'Active' 
                     AND id != ?""",
                (cleaned_name, int(exclude_member_id)), fetchone=True,
            )
        else:
            row = self.db.execute(
                """SELECT id FROM members 
                   WHERE TRIM(full_name) = TRIM(?) 
                     AND status = 'Active'""", 
                (cleaned_name,), fetchone=True
            )
        return row is not None
    
    def get_member_detailed_financial_report(self, member_id):
        """جلب تفاصيل اللجان المشترك بها والجلسات التي حضرها أو غاب عنها وقيم الصرف الفعلي لها"""
        # 1. جلب تفاصيل اللجان والمكافآت
        committees_query = """
            SELECT c.name as committee_name, cm.role, cm.bonus_amount, cm.attendance_allowance as session_rate
            FROM committee_members cm
            JOIN committees c ON cm.committee_id = c.id
            WHERE cm.member_id = ?
        """
        committees = self.db.execute(committees_query, (member_id,), fetchall=True)
        
        # 2. جلب تفاصيل الجلسات (سواء حضور أو غياب) والمبالغ المدفوعة فعلياً
        meetings_query = """
            SELECT m.name as meeting_name, m.meeting_date, m.session_type,
                   af.attended, af.amount_paid
            FROM attendance_financials af
            JOIN meetings m ON af.meeting_id = m.id
            WHERE af.member_id = ?
            ORDER BY m.meeting_date DESC
        """
        meetings = self.db.execute(meetings_query, (member_id,), fetchall=True)
        
        return {
            "committees": [dict(c) for c in committees],
            "meetings": [dict(m) for m in meetings]
        }